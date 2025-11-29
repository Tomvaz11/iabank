from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from http import HTTPStatus
from typing import Any, Dict, Optional
from uuid import UUID

import structlog
from django.db import connection, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedBatch, SeedCheckpoint, SeedProfile, SeedRun
from backend.apps.tenancy.services.budget import BudgetService, BudgetSnapshot
from backend.apps.tenancy.services.seed_manifest_validator import (
    SeedManifestValidator,
    compute_manifest_hash,
)
from backend.apps.tenancy.services.seed_dataset_gc import SeedDatasetGC
from backend.apps.tenancy.services.seed_queue import QueueDecision, SeedQueueService

logger = structlog.get_logger('seed.telemetry')


@dataclass
class ProblemDetail:
    status: int
    title: str
    detail: str
    type: str
    retry_after: Optional[int] = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            'status': self.status,
            'title': self.title,
            'detail': self.detail,
            'type': self.type,
        }
        if self.retry_after is not None:
            payload['retry_after'] = self.retry_after
        return payload


@dataclass
class SeedRunCreation:
    seed_run: SeedRun
    seed_profile: SeedProfile
    batches: list[SeedBatch]


@dataclass
class _ManifestParts:
    reference_datetime: datetime
    window_start: time
    window_end: time
    volumetry: Dict[str, Any]
    rate_limit: Dict[str, Any]
    backoff: Dict[str, Any]
    budget: Dict[str, Any]
    ttl_config: Dict[str, Any]
    slo: Dict[str, Any]
    integrity: Dict[str, Any]
    metadata: Dict[str, Any]
    canary_scope: Any
    manifest_hash: str


def _trace_ids_from_context() -> tuple[str, str]:
    """
    Retorna trace_id/span_id do contexto OTEL atual, se disponível.
    Mantém comportamento noop quando OTEL não está instalado.
    """
    try:
        from opentelemetry import trace  # type: ignore

        span = trace.get_current_span()
        context = span.get_span_context()
        if context and context.is_valid:
            trace_id = format(context.trace_id, '032x')
            span_id = format(context.span_id, '016x')
            return trace_id, span_id
    except Exception:
        return '', ''
    return '', ''


def _seed_log_context(
    *,
    seed_profile: SeedProfile,
    manifest_hash: str,
    seed_run_id: UUID | None = None,
    mode: str,
    dry_run: bool,
) -> dict[str, object]:
    return {
        'tenant_id': str(seed_profile.tenant_id),
        'environment': seed_profile.environment,
        'manifest_version': seed_profile.version,
        'manifest_hash': manifest_hash,
        'mode': mode,
        'dry_run': dry_run,
        'seed_run_id': str(seed_run_id) if seed_run_id else None,
    }


class SeedRunService:
    def __init__(
        self,
        queue_service: Optional[SeedQueueService] = None,
        budget_service: Optional[BudgetService] = None,
        dataset_gc: Optional[SeedDatasetGC] = None,
    ) -> None:
        self.queue_service = queue_service or SeedQueueService()
        self.budget_service = budget_service or BudgetService()
        self.dataset_gc = dataset_gc or SeedDatasetGC()

    def ensure_reference_drift(
        self,
        *,
        tenant_id: UUID,
        environment: str,
        mode: str,
        reference_datetime: datetime,
    ) -> Optional[ProblemDetail]:
        """
        Bloqueia execução quando já existem checkpoints para um reference_datetime diferente.
        """
        with use_tenant(tenant_id):
            checkpoints = (
                SeedCheckpoint.objects.select_related('seed_run')
                .filter(seed_run__environment=environment, seed_run__mode=mode)
                .all()
            )

        for checkpoint in checkpoints:
            run = checkpoint.seed_run
            if run and run.reference_datetime != reference_datetime:
                return ProblemDetail(
                    status=HTTPStatus.UNPROCESSABLE_ENTITY,
                    title='reference_datetime_drift',
                    detail=(
                        'Reference datetime do manifesto diverge de checkpoints existentes. '
                        'Limpe checkpoints/seed datasets antes de forçar novo seed_data.'
                    ),
                    type='https://iabank.local/problems/seed/reference-drift',
                )
        return None

    def create_seed_run(
        self,
        *,
        tenant_id: UUID,
        environment: str,
        manifest: Dict[str, Any],
        manifest_path: str,
        idempotency_key: str,
        requested_by: str,
        dry_run: bool,
        mode: str,
    ) -> SeedRunCreation:
        parts = self._extract_manifest_parts(
            manifest=manifest,
            manifest_path=manifest_path,
            mode=mode,
        )

        ttl_days = self._ttl_for_mode(parts.ttl_config, mode)
        if self.dataset_gc:
            self.dataset_gc.cleanup_for_mode(
                tenant_id=tenant_id,
                environment=environment,
                mode=mode,
            )
            if ttl_days > 0:
                self.dataset_gc.expire_by_ttl(
                    tenant_id=tenant_id,
                    days=ttl_days,
                    environment=environment,
                )

        snapshot = None
        with transaction.atomic():
            if not self._acquire_advisory_lock(tenant_id, environment):
                raise RuntimeError('Não foi possível adquirir lock para o seed_data.')  # pragma: no cover

            with use_tenant(tenant_id):
                seed_profile = self._upsert_seed_profile(
                    tenant_id=tenant_id,
                    environment=environment,
                    mode=mode,
                    manifest_path=manifest_path,
                    parts=parts,
                )

                if self.budget_service:
                    snapshot = self.budget_service.snapshot_from_profile(seed_profile)
                    self.budget_service.ensure_budget_for_profile(seed_profile, snapshot=snapshot)

                rate_limit_usage = self._rate_limit_usage(snapshot=snapshot, parts=parts)
                seed_run = self._create_seed_run_record(
                    seed_profile=seed_profile,
                    environment=environment,
                    mode=mode,
                    requested_by=requested_by,
                    idempotency_key=idempotency_key,
                    manifest_path=manifest_path,
                    dry_run=dry_run,
                    parts=parts,
                    rate_limit_usage=rate_limit_usage,
                )

                batches = self._create_batches(seed_run, parts.volumetry)

        return SeedRunCreation(seed_run=seed_run, seed_profile=seed_profile, batches=batches)

    def _extract_manifest_parts(self, *, manifest: Dict[str, Any], manifest_path: str, mode: str) -> _ManifestParts:
        manifest_dict = manifest if isinstance(manifest, dict) else {}
        metadata = manifest_dict.get('metadata') or {}
        volumetry = manifest_dict.get('volumetry') or {}
        rate_limit = manifest_dict.get('rate_limit') or {}
        backoff = manifest_dict.get('backoff') or {}
        budget = manifest_dict.get('budget') or {}
        ttl_config = manifest_dict.get('ttl') or {}
        slo = manifest_dict.get('slo') or {}
        integrity = manifest_dict.get('integrity') or {}
        canary_scope = manifest_dict.get('canary')
        manifest_hash = compute_manifest_hash(manifest_dict)
        window_start, window_end = self._extract_window(manifest_dict)

        return _ManifestParts(
            reference_datetime=self._parse_reference_datetime(manifest_dict),
            window_start=window_start,
            window_end=window_end,
            volumetry=volumetry,
            rate_limit=rate_limit,
            backoff=backoff,
            budget=budget,
            ttl_config=ttl_config,
            slo=slo,
            integrity=integrity,
            metadata=metadata,
            canary_scope=canary_scope,
            manifest_hash=manifest_hash,
        )

    def _upsert_seed_profile(
        self,
        *,
        tenant_id: UUID,
        environment: str,
        mode: str,
        manifest_path: str,
        parts: _ManifestParts,
    ) -> SeedProfile:
        with use_tenant(tenant_id):
            seed_profile, _ = SeedProfile.objects.update_or_create(
                profile=parts.metadata.get('profile', 'default'),
                version=parts.metadata.get('version', '0.0.0'),
                defaults={
                    'environment': environment,
                    'schema_version': parts.metadata.get('schema_version', 'v1'),
                    'mode': mode,
                    'reference_datetime': parts.reference_datetime,
                    'volumetry': parts.volumetry or {},
                    'rate_limit': parts.rate_limit or {},
                    'backoff': parts.backoff or {},
                    'budget': parts.budget or {},
                    'window_start_utc': parts.window_start,
                    'window_end_utc': parts.window_end,
                    'ttl_config': parts.ttl_config or {},
                    'slo_p95_ms': int(parts.slo.get('p95_target_ms', 0) or 0),
                    'slo_p99_ms': int(parts.slo.get('p99_target_ms', 0) or 0),
                    'slo_throughput_rps': Decimal(str(parts.slo.get('throughput_target_rps', 0) or 0)),
                    'integrity_hash': parts.integrity.get('manifest_hash', parts.manifest_hash),
                    'manifest_path': manifest_path,
                    'manifest_hash_sha256': parts.manifest_hash,
                    'salt_version': parts.metadata.get('salt_version', 'v1'),
                    'canary_scope': parts.canary_scope,
                },
            )
        return seed_profile

    def _create_seed_run_record(
        self,
        *,
        seed_profile: SeedProfile,
        environment: str,
        mode: str,
        requested_by: str,
        idempotency_key: str,
        manifest_path: str,
        dry_run: bool,
        parts: _ManifestParts,
        rate_limit_usage: Dict[str, Any] | None,
    ) -> SeedRun:
        trace_id, span_id = _trace_ids_from_context()
        seed_run = SeedRun.objects.create(
            seed_profile=seed_profile,
            environment=environment,
            mode=mode,
            status=SeedRun.Status.QUEUED,
            requested_by=requested_by,
            idempotency_key=idempotency_key,
            manifest_path=manifest_path,
            manifest_hash_sha256=parts.manifest_hash,
            reference_datetime=parts.reference_datetime,
            profile_version=parts.metadata.get('version', ''),
            dry_run=dry_run,
            offpeak_window={'start': parts.window_start.isoformat(), 'end': parts.window_end.isoformat()},
            canary_scope_snapshot=parts.canary_scope,
            rate_limit_usage=rate_limit_usage or {},
            trace_id=trace_id or None,
            span_id=span_id or None,
        )
        logger.info(
            'seed_run_enqueued',
            **_seed_log_context(
                seed_profile=seed_profile,
                manifest_hash=parts.manifest_hash,
                seed_run_id=seed_run.id,
                mode=mode,
                dry_run=dry_run,
            ),
            trace_id=trace_id or seed_run.trace_id,
            span_id=span_id or seed_run.span_id,
        )
        return seed_run

    def request_slot(
        self,
        *,
        environment: str,
        tenant_id: UUID,
        seed_run_id: Optional[UUID] = None,
        now: Optional[datetime] = None,
        ttl: Optional[timedelta] = None,
    ) -> tuple[QueueDecision, Optional[ProblemDetail]]:
        current_time = now or timezone.now()
        decision = self.queue_service.enqueue(
            environment=environment,
            tenant_id=tenant_id,
            seed_run_id=seed_run_id,
            now=current_time,
            ttl=ttl,
        )

        if decision.allowed:
            return decision, None

        return decision, self._build_problem(decision=decision, environment=environment)

    @staticmethod
    def exit_code_for(decision: QueueDecision) -> int:
        if decision.status_code == HTTPStatus.CONFLICT:
            return 3
        if decision.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            return 5
        return 1

    @staticmethod
    def _build_problem(decision: QueueDecision, environment: str) -> ProblemDetail:
        if decision.status_code == HTTPStatus.CONFLICT:
            return ProblemDetail(
                status=HTTPStatus.CONFLICT,
                title='global_concurrency_cap',
                detail=f'Limite global de execuções ativas atingido no ambiente {environment}.',
                type='https://iabank.local/problems/seed/global-cap',
                retry_after=decision.retry_after,
            )

        return ProblemDetail(
            status=HTTPStatus.TOO_MANY_REQUESTS,
            title='seed_queue_busy',
            detail=f'A fila de seeds do ambiente {environment} ainda possui itens pendentes dentro do TTL.',
            type='https://iabank.local/problems/seed/queue-ttl',
            retry_after=decision.retry_after,
        )

    @staticmethod
    def exit_code_for_problem(problem: ProblemDetail) -> int:
        if problem.status in {HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY, HTTPStatus.CONFLICT}:
            return 2
        if problem.status == HTTPStatus.TOO_MANY_REQUESTS:
            return 5
        return 1

    @staticmethod
    def _parse_reference_datetime(manifest: Dict[str, Any]) -> datetime:
        raw = manifest.get('reference_datetime') if isinstance(manifest, dict) else None
        parsed = parse_datetime(str(raw)) if raw is not None else None
        return parsed or timezone.now()

    @staticmethod
    def _in_offpeak_window(reference: datetime, window_start: time, window_end: time) -> bool:
        """
        Avalia se a referência informada cai na janela off-peak.
        """
        ref_time = reference.time()
        if window_start <= window_end:
            return window_start <= ref_time <= window_end
        return ref_time >= window_start or ref_time <= window_end

    def ensure_offpeak_window(
        self,
        *,
        manifest: Dict[str, Any],
        environment: str,
        mode: str,
    ) -> Optional[ProblemDetail]:
        """
        Bloqueia execuções fora da janela off-peak declarada no manifesto, exceto se override explícito.
        """
        if manifest.get('allow_offpeak_override'):
            return None

        window_start, window_end = self._extract_window(manifest)
        reference = self._parse_reference_datetime(manifest)
        if self._in_offpeak_window(reference, window_start, window_end):
            return None

        return ProblemDetail(
            status=HTTPStatus.FORBIDDEN,
            title='offpeak_window_closed',
            detail=f'Janela off-peak para {environment}/{mode} está fechada.',
            type='https://iabank.local/problems/seed/offpeak-closed',
        )

    def ensure_environment_gate(self, *, environment: str, mode: str) -> Optional[ProblemDetail]:
        """
        Bloqueia modos carga/DR fora dos ambientes permitidos pelo cost-model (WORM).
        """
        if mode not in {'carga', 'dr'} or self.budget_service is None:
            return None

        if self.budget_service.environment_allowed(mode=mode, environment=environment):
            return None

        required = sorted(self.budget_service.required_environments())
        detail = (
            f'Modo {mode} exige execução em ambientes dedicados (ex.: {", ".join(required)}) '
            'com WORM habilitado e rollback validado.'
        )
        return ProblemDetail(
            status=HTTPStatus.FORBIDDEN,
            title='environment_not_allowed_for_mode',
            detail=detail,
            type='https://iabank.local/problems/seed/environment-gate',
        )

    def ensure_worm_evidence(self, *, manifest: Dict[str, Any], mode: str) -> Optional[ProblemDetail]:
        """
        Bloqueia execuções carga/DR quando o manifesto não declara evidência WORM exigida.
        """
        if mode not in {'carga', 'dr'} or self.budget_service is None:
            return None

        if not self.budget_service.worm_required(mode):
            return None

        integrity = manifest.get('integrity') if isinstance(manifest, dict) else {}
        worm_proof = integrity.get('worm_proof') if isinstance(integrity, dict) else None
        if worm_proof:
            return None

        return ProblemDetail(
            status=HTTPStatus.FORBIDDEN,
            title='worm_evidence_missing',
            detail='Execuções de carga/DR exigem evidência WORM válida antes da promoção.',
            type='https://iabank.local/problems/seed/worm-evidence',
        )

    def ensure_cost_model_alignment(self, *, manifest: Dict[str, Any]) -> Optional[ProblemDetail]:
        """
        Valida se a versão de cost-model declarada no manifesto está alinhada ao arquivo atual.
        """
        if self.budget_service is None:
            return None

        budget_cfg = manifest.get('budget') if isinstance(manifest, dict) else {}
        manifest_version = budget_cfg.get('cost_model_version') if isinstance(budget_cfg, dict) else None
        if not manifest_version:
            return None

        model_version = str(self.budget_service.cost_model.get('model_version', '')).strip()
        if manifest_version == model_version:
            return None

        return ProblemDetail(
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
            title='cost_model_mismatch',
            detail=f'Versão do cost-model no manifesto ({manifest_version}) diverge da versão ativa ({model_version}).',
            type='https://iabank.local/problems/seed/cost-model-version',
        )

    def ensure_manifest_gitops_alignment(
        self,
        *,
        manifest_path: str,
        environment: str,
        allow_local_override: bool = False,
    ) -> Optional[ProblemDetail]:
        """
        Garante que o manifesto esteja no caminho GitOps esperado para evitar drift no Argo CD.
        """
        expected_prefix = f'configs/seed_profiles/{environment}/'
        if manifest_path and manifest_path.startswith(expected_prefix):
            return None

        if allow_local_override and manifest_path:
            lowered = manifest_path.lower()
            if lowered.startswith('/tmp') or lowered.startswith('tmp/'):
                return None
            if '/pytest-' in lowered:
                return None

        return ProblemDetail(
            status=HTTPStatus.CONFLICT,
            title='gitops_drift',
            detail=f'Manifesto deve residir em {expected_prefix}*.yaml para promoção segura/GitOps.',
            type='https://iabank.local/problems/seed/gitops-drift',
        )

    @staticmethod
    def queue_ttl_for_mode(mode: str) -> timedelta:
        """
        TTL diferenciado para fila por modo; baseline mantém 5min para evitar backlog.
        """
        if mode in {'carga', 'dr'}:
            return timedelta(minutes=10)
        return timedelta(minutes=5)

    @staticmethod
    def _extract_window(manifest: Dict[str, Any]) -> tuple[time, time]:
        window = manifest.get('window') if isinstance(manifest, dict) else {}
        start_raw = window.get('start_utc', '00:00')
        end_raw = window.get('end_utc', '06:00')
        try:
            start = time.fromisoformat(str(start_raw))
        except ValueError:
            start = time.fromisoformat('00:00')
        try:
            end = time.fromisoformat(str(end_raw))
        except ValueError:
            end = time.fromisoformat('06:00')
        return start, end

    def _rate_limit_usage(self, *, snapshot: BudgetSnapshot | None, parts: _ManifestParts) -> dict[str, Any]:
        if snapshot:
            limit = snapshot.limit
            window_seconds = snapshot.window_seconds
        else:
            limit = max(1, int(parts.rate_limit.get('limit', 1) or 1))
            window_seconds = max(1, int(parts.rate_limit.get('window_seconds', 60) or 60))
        reset_at = timezone.now() + timedelta(seconds=window_seconds)
        return {'limit': limit, 'remaining': limit, 'reset_at': reset_at.isoformat()}

    @staticmethod
    def _ttl_for_mode(ttl_config: Dict[str, Any], mode: str) -> int:
        key = f'{mode}_days'
        if not isinstance(ttl_config, dict):
            return 0
        try:
            return int(ttl_config.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _create_batches(seed_run: SeedRun, volumetry: Dict[str, Any]) -> list[SeedBatch]:
        ordered_entities = [
            'tenant_users',
            'customers',
            'addresses',
            'consultants',
            'bank_accounts',
            'account_categories',
            'suppliers',
            'loans',
            'installments',
            'financial_transactions',
            'limits',
            'contracts',
        ]

        batches: list[SeedBatch] = []
        volumetry_caps = SeedManifestValidator.extract_caps({'volumetry': volumetry})

        for entity in ordered_entities:
            cap = volumetry_caps.get(entity)
            if cap is None:
                continue
            snapshot = volumetry.get(entity, {}) if isinstance(volumetry, dict) else {}
            batches.append(
                SeedBatch(
                    seed_run=seed_run,
                    tenant=seed_run.tenant,
                    entity=entity,
                    batch_size=max(1, int(cap)),
                    caps_snapshot=snapshot,
                )
            )

        with use_tenant(seed_run.tenant_id):
            SeedBatch.objects.bulk_create(batches)
        return batches

    @staticmethod
    def _acquire_advisory_lock(tenant_id: UUID, environment: str) -> bool:
        """
        Serializa criação de SeedRun por tenant/ambiente usando pg_try_advisory_xact_lock.
        """
        key = abs(hash((str(tenant_id), environment))) % (2**63)
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_try_advisory_xact_lock(%s)', [key])
            locked = cursor.fetchone()
        return bool(locked and locked[0])
