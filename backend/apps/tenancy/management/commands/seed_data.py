from __future__ import annotations

import json
import os
import sys
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import Tenant
from backend.apps.tenancy.services.seed_preflight import PreflightContext, SeedPreflightService
from backend.apps.tenancy.services.seed_runs import SeedRunService


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

    def handle(self, *args, **options) -> None:
        tenant_id = self._parse_tenant_id(options['tenant_id'])
        environment = options['environment']
        mode = options['mode']
        dry_run = bool(options.get('dry_run', False))

        tenant = self._get_tenant(tenant_id)
        requested_by, roles, manifest_path = self._preflight_params(options, tenant.slug, environment)
        self._run_preflight(tenant.id, environment, requested_by, roles, manifest_path, dry_run)

        with use_tenant(tenant.id):
            service = SeedRunService()
            decision, problem = service.request_slot(
                environment=environment,
                tenant_id=tenant.id,
                seed_run_id=None,
                now=timezone.now(),
            )

        if problem:
            self.stderr.write(self.style.WARNING(json.dumps(problem.as_dict())))
            sys.exit(service.exit_code_for(decision))

        entry = decision.entry
        message = (
            f'Seed {mode} {"(dry-run)" if dry_run else ""} '
            f'aceito na fila {decision.reason} para {environment}.'
        )
        self.stdout.write(self.style.SUCCESS(message))

        if entry:
            self.stdout.write(f'queue_entry={entry.id} expires_at={entry.expires_at.isoformat()}')

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
