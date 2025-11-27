from __future__ import annotations

import json
import sys
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import Tenant
from backend.apps.tenancy.services.seed_runs import SeedRunService


class Command(BaseCommand):
    help = 'Executa seeds baseline/carga/DR respeitando fila global com TTL e acks tardios.'

    def add_arguments(self, parser) -> None:
        parser.add_argument('--tenant-id', required=True, help='Tenant alvo (UUID).')
        parser.add_argument('--environment', required=True, help='Ambiente alvo (ex.: dev, staging).')
        parser.add_argument('--mode', default='baseline', help='Modo de execução do seed.')
        parser.add_argument('--dry-run', action='store_true', help='Executa em modo dry-run.')

    def handle(self, *args, **options) -> None:
        try:
            tenant_id = UUID(options['tenant_id'])
        except (TypeError, ValueError) as exc:  # pragma: no cover - validação simples de CLI
            raise CommandError(f'Tenant inválido: {exc}') from exc

        environment = options['environment']
        mode = options['mode']
        dry_run = bool(options.get('dry_run', False))

        tenant = Tenant.objects.filter(id=tenant_id).first()
        if tenant is None:
            raise CommandError(f'Tenant {tenant_id} não encontrado.')

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
