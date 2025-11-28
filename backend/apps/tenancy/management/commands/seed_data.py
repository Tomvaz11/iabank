from __future__ import annotations

import json
import os
import sys
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Tuple
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from backend.apps.tenancy.feature_flags import SeedDORAMetrics, SeedFeatureFlags
from backend.apps.tenancy import tasks as seed_tasks
from backend.apps.tenancy.managers import _set_tenant_guc, _current_tenant, use_tenant
from backend.apps.tenancy.models import Tenant
from backend.apps.tenancy.services.seed_integrations import SeedIntegrationService
from backend.apps.tenancy.services.seed_idempotency import IdempotencyDecision, SeedIdempotencyService
from backend.apps.tenancy.services.seed_manifest_validator import SeedManifestValidator, ValidationResult
from backend.apps.tenancy.services.seed_preflight import PreflightContext, SeedPreflightService
from backend.apps.tenancy.services.seed_queue_gc import SeedQueueGC
from backend.apps.tenancy.services.seed_runs import ProblemDetail, SeedRunService


class Command(BaseCommand):
    help = 'Executa seeds baseline/carga/DR respeitando fila global com TTL e acks tardios.'

    def add_arguments(self, parser) -> None:
        parser.add_argument('--tenant-id', required=True, help='Tenant alvo (UUID).')
        parser.add_argument('--environment', required=True, help='Ambiente alvo (ex.: dev, staging).')
        parser.add_argument('--mode', default='baseline', help='Modo de execução do seed.')
        parser.add_argument('--dry-run', action='store_true', help='Executa em modo dry-run.')
        parser.add_argument('--requested-by', help='Identificador de quem requisitou (svc/usuário).')
        parser.add_argument(
            '--role',
            action='append',
            dest='roles',
            help='Role autorizada (pode repetir; ex.: --role seed-runner --role seed-admin).',
        )
        parser.add_argument('--manifest-path', help='Caminho do manifesto para auditoria/fingerprint.')
        parser.add_argument(
            '--idempotency-key',
            help='Chave de idempotência (default = hash do manifesto).',
        )

    def handle(self, *args, **options) -> None:
        tenant_id = self._parse_tenant_id(options['tenant_id'])
        environment = options['environment']
        mode = options['mode']
        dry_run = bool(options.get('dry_run', False))
        feature_flags = SeedFeatureFlags()
        integration_service = SeedIntegrationService()

        tenant = self._get_tenant(tenant_id)
        self._pin_tenant_context(tenant.id)
        requested_by, roles, manifest_path = self._preflight_params(options, tenant.slug, environment)
        self._run_preflight(tenant.id, environment, requested_by, roles, manifest_path, dry_run)

        manifest, manifest_hash, mode, reference_datetime, validation, from_file = self._prepare_manifest(
            manifest_path,
            tenant.slug,
            environment,
            mode,
        )
        self._ensure_manifest_matches_tenant(validation, from_file, manifest, tenant.slug)

        service = SeedRunService()
        queue_gc = SeedQueueGC()
        self._fail_if_problem(
            service.ensure_reference_drift(
                tenant_id=tenant.id,
                environment=environment,
                mode=mode,
                reference_datetime=reference_datetime,
            ),
            service.exit_code_for_problem,
        )
        self._fail_if_problem(
            service.ensure_offpeak_window(
                manifest=manifest,
                environment=environment,
                mode=mode,
            ),
            service.exit_code_for_problem,
        )
        self._fail_if_problem(
            service.ensure_environment_gate(
                environment=environment,
                mode=mode,
            ),
            service.exit_code_for_problem,
        )
        self._fail_if_problem(
            service.ensure_cost_model_alignment(manifest=manifest),
            service.exit_code_for_problem,
        )
        self._fail_if_problem(
            integration_service.block_outbound(manifest=manifest),
            service.exit_code_for_problem,
        )
        self._fail_if_problem(
            feature_flags.ensure_canary_scope(
                manifest=manifest,
                mode=mode,
            ),
            service.exit_code_for_problem,
        )
        self._fail_if_problem(
            service.ensure_worm_evidence(manifest=manifest, mode=mode),
            service.exit_code_for_problem,
        )
        self._fail_if_problem(
            service.ensure_manifest_gitops_alignment(
                manifest_path=manifest_path,
                environment=environment,
                allow_local_override=dry_run,
            ),
            service.exit_code_for_problem,
        )

        idempotency_service = SeedIdempotencyService(tenant.id, context='seed_data_cli')
        idempotency_service.cleanup_expired(environment=environment)
        idempotency_key = self._resolve_idempotency_key(options, manifest_hash)
        idempotency_decision, created_idempo_entry = self._ensure_idempotency(
            idempotency_service=idempotency_service,
            environment=environment,
            idempotency_key=idempotency_key,
            manifest_hash=manifest_hash,
            mode=mode,
        )
        if idempotency_decision is None:
            return

        queue_gc.expire_stale(environment=environment)
        with use_tenant(tenant.id):
            decision, problem = service.request_slot(
                environment=environment,
                tenant_id=tenant.id,
                seed_run_id=None,
                now=timezone.now(),
                ttl=SeedRunService.queue_ttl_for_mode(mode),
            )

        if problem:
            self._cleanup_idempotency(created_idempo_entry, idempotency_decision, tenant.id)
            self._render_problem(problem, exit_code=service.exit_code_for(decision))

        creation = service.create_seed_run(
            tenant_id=tenant.id,
            environment=environment,
            manifest=manifest,
            manifest_path=manifest_path,
            idempotency_key=idempotency_key,
            requested_by=requested_by,
            dry_run=dry_run,
            mode=mode,
        )

        if idempotency_decision.entry:
            with use_tenant(tenant.id):
                idempotency_decision.entry.seed_run = creation.seed_run
                idempotency_decision.entry.save(update_fields=['seed_run', 'updated_at'])

        entry = decision.entry
        if entry:
            entry.seed_run = creation.seed_run
            entry.tenant = creation.seed_run.tenant
            entry.save(update_fields=['seed_run', 'tenant', 'updated_at'])

        message = (
            f'Seed {mode} {"(dry-run)" if dry_run else ""} '
            f'aceito na fila {decision.reason} para {environment}. '
            f'seed_run={creation.seed_run.id}'
        )
        self.stdout.write(self.style.SUCCESS(message))
        self.stdout.write(f'manifest_hash={manifest_hash}')
        if entry:
            self.stdout.write(f'queue_entry={entry.id} expires_at={entry.expires_at.isoformat()}')
        self._dispatch_batches(creation, mode)
        SeedDORAMetrics().snapshot(seed_run=creation.seed_run)

    def _load_manifest(
        self,
        manifest_path: str,
        tenant_slug: str,
        environment: str,
        mode: str,
    ) -> Tuple[Dict[str, Any], bool]:
        path = Path(manifest_path)
        if path.exists():
            content = path.read_text(encoding='utf-8')
            parsed = self._parse_manifest_content(content)
            return parsed if isinstance(parsed, dict) else {}, True
        return self._default_manifest(tenant_slug, environment, mode), False

    def _parse_manifest_content(self, content: str) -> Dict[str, Any]:
        try:
            import yaml  # type: ignore
        except Exception:  # pragma: no cover - fallback quando PyYAML não estiver disponível
            yaml = None

        if yaml is not None:
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict):
                    return data
            except yaml.YAMLError:
                pass

        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return {}
        return {}

    def _default_manifest(self, tenant_slug: str, environment: str, mode: str) -> Dict[str, Any]:
        return {
            'metadata': {
                'tenant': tenant_slug,
                'environment': environment,
                'profile': 'default',
                'version': '0.0.0',
                'schema_version': 'v1',
                'salt_version': 'v1',
            },
            'mode': mode or 'baseline',
            'reference_datetime': '2025-01-01T00:00:00Z',
            'window': {'start_utc': '00:00', 'end_utc': '06:00'},
            'volumetry': {},
            'rate_limit': {'limit': 1, 'window_seconds': 60},
            'backoff': {'base_seconds': 1, 'jitter_factor': 0.1, 'max_retries': 1, 'max_interval_seconds': 60},
            'budget': {'cost_cap_brl': 0, 'error_budget_pct': 0},
            'ttl': {'baseline_days': 0, 'carga_days': 0, 'dr_days': 0},
            'slo': {'p95_target_ms': 0, 'p99_target_ms': 0, 'throughput_target_rps': 0},
            'integrity': {'manifest_hash': ''},
        }

    def _apply_manifest_hash(self, manifest: Dict[str, Any], manifest_hash: str) -> Dict[str, Any]:
        integrity = manifest.get('integrity') if isinstance(manifest, dict) else None
        if not isinstance(integrity, dict):
            manifest['integrity'] = {'manifest_hash': manifest_hash}
        else:
            integrity.setdefault('manifest_hash', manifest_hash)
        return manifest

    def _dispatch_batches(self, creation, mode: str) -> None:
        """
        Dispara tasks Celery para cada batch criado.
        Por padrão roda de forma síncrona (sem broker) para testes/dev; habilite async com SEED_CELERY_ASYNC=1.
        """
        use_async = os.getenv('SEED_CELERY_ASYNC', '0') == '1'
        queue = 'seed_data.load_dr' if mode in {'carga', 'dr'} else 'seed_data.default'
        task = seed_tasks.dispatch_load_dr if queue == 'seed_data.load_dr' else seed_tasks.dispatch_baseline
        for batch in creation.batches:
            args = [str(batch.seed_run_id), str(batch.tenant_id)]
            if use_async:
                task.apply_async(args=args, queue=queue)  # pragma: no cover - integração real com broker
            else:
                fake_self = SimpleNamespace(request=SimpleNamespace(delivery_info={'routing_key': queue}))
                task.__wrapped__.__func__(fake_self, *args)  # type: ignore[attr-defined]

    def _resolve_idempotency_key(self, options: dict, manifest_hash: str) -> str:
        explicit = options.get('idempotency_key') or os.getenv('SEED_IDEMPOTENCY_KEY')
        if explicit:
            return str(explicit)
        return f'seed-data:{manifest_hash or "auto"}'

    def _prepare_manifest(
        self,
        manifest_path: str,
        tenant_slug: str,
        environment: str,
        mode: str,
    ) -> tuple[Dict[str, Any], str, str, timezone.datetime, ValidationResult, bool]:
        manifest, from_file = self._load_manifest(manifest_path, tenant_slug, environment, mode)
        validator = SeedManifestValidator()
        validation = validator.validate_manifest(manifest, environment=environment)
        manifest_hash = validation.manifest_hash
        manifest = self._apply_manifest_hash(manifest, manifest_hash)
        resolved_mode = manifest.get('mode', mode) or mode
        reference_datetime = SeedRunService._parse_reference_datetime(manifest)
        return manifest, manifest_hash, resolved_mode, reference_datetime, validation, from_file

    def _ensure_manifest_matches_tenant(
        self,
        validation: ValidationResult,
        from_file: bool,
        manifest: Dict[str, Any],
        tenant_slug: str,
    ) -> None:
        if from_file and not validation.valid:
            self._render_problem(
                ProblemDetail(
                    status=HTTPStatus.UNPROCESSABLE_ENTITY,
                    title='manifest_invalid',
                    detail='; '.join(validation.issues),
                    type='https://iabank.local/problems/seed/manifest-invalid',
                ),
                exit_code=2,
            )

        tenant_in_manifest = manifest.get('metadata', {}).get('tenant')
        if tenant_in_manifest and tenant_in_manifest != tenant_slug:
            self._render_problem(
                ProblemDetail(
                    status=HTTPStatus.UNPROCESSABLE_ENTITY,
                    title='manifest_tenant_mismatch',
                    detail='Manifesto pertence a outro tenant; revise o caminho informado.',
                    type='https://iabank.local/problems/seed/tenant-mismatch',
                ),
                exit_code=2,
            )

    def _fail_if_problem(self, problem: ProblemDetail | None, exit_code_resolver) -> None:
        if problem:
            self._render_problem(problem, exit_code=exit_code_resolver(problem))

    def _ensure_idempotency(
        self,
        *,
        idempotency_service: SeedIdempotencyService,
        environment: str,
        idempotency_key: str,
        manifest_hash: str,
        mode: str,
    ) -> tuple[IdempotencyDecision | None, bool]:
        decision = idempotency_service.ensure_entry(
            environment=environment,
            idempotency_key=idempotency_key,
            manifest_hash=manifest_hash,
            mode=mode,
        )
        created = decision.outcome == 'new'

        if decision.outcome == 'conflict':
            self._render_problem(
                ProblemDetail(
                    status=HTTPStatus.CONFLICT,
                    title='idempotency_conflict',
                    detail='Idempotency-Key já usada para manifesto diferente; limpe ou use nova chave.',
                    type='https://iabank.local/problems/seed/idempotency-conflict',
                ),
                exit_code=2,
            )

        if decision.outcome == 'replay' and decision.entry and decision.entry.seed_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Replay idempotente: reutilizando SeedRun {decision.entry.seed_run_id} para {environment}.',
                )
            )
            return None, created

        return decision, created

    def _cleanup_idempotency(
        self,
        created: bool,
        decision: IdempotencyDecision,
        tenant_id: UUID,
    ) -> None:
        if created and decision.entry:
            with use_tenant(tenant_id):
                decision.entry.delete()

    def _render_problem(self, problem: ProblemDetail, *, exit_code: int) -> None:
        self.stderr.write(self.style.ERROR(json.dumps(problem.as_dict())))
        sys.exit(exit_code)

    def _pin_tenant_context(self, tenant_id: UUID) -> None:
        """
        Mantém o tenant atual no contexto para consultas pós-comando em testes.
        """
        _current_tenant.set(str(tenant_id))
        _set_tenant_guc(str(tenant_id))

    def _parse_tenant_id(self, raw: str) -> UUID:
        try:
            return UUID(raw)
        except (TypeError, ValueError) as exc:  # pragma: no cover - validação simples de CLI
            raise CommandError(f'Tenant inválido: {exc}') from exc

    def _get_tenant(self, tenant_id: UUID) -> Tenant:
        tenant = Tenant.objects.filter(id=tenant_id).first()
        if tenant is None:
            raise CommandError(f'Tenant {tenant_id} não encontrado.')
        return tenant

    def _preflight_params(self, options: dict, tenant_slug: str, environment: str) -> tuple[str, list[str], str]:
        requested_by = options.get('requested_by') or os.getenv('SEED_REQUESTED_BY', 'cli:seed-data')
        roles_env = os.getenv('SEED_ROLES', 'seed-runner')
        roles = options.get('roles') or roles_env.split(',')
        manifest_path = options.get('manifest_path') or f'configs/seed_profiles/{environment}/{tenant_slug}.yaml'
        return requested_by, roles, manifest_path

    def _run_preflight(
        self,
        tenant_id: UUID,
        environment: str,
        requested_by: str,
        roles: list[str],
        manifest_path: str,
        dry_run: bool,
    ) -> None:
        preflight_service = SeedPreflightService()
        context = PreflightContext(
            tenant_id=str(tenant_id),
            environment=environment,
            manifest_path=manifest_path,
            requested_by=requested_by,
            roles=roles,
            dry_run=dry_run,
        )
        preflight = preflight_service.check(context)
        if preflight.allowed:
            return

        problem = preflight.problem
        if problem:
            self.stderr.write(self.style.ERROR(json.dumps(problem.as_dict())))
        else:  # pragma: no cover - fallback defensivo
            self.stderr.write(self.style.ERROR('Preflight falhou sem detalhe.'))
        sys.exit(1)
