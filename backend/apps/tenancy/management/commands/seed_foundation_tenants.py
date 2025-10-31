from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from backend.apps.tenancy.models import Tenant, TenantThemeToken


ROOT_DIR = Path(__file__).resolve().parents[5]
CACHE_DIR = ROOT_DIR / 'frontend' / 'scripts' / 'tokens' / 'cache'

DEMO_TENANTS: list[dict[str, Any]] = [
    {
        'id': UUID('00000000-0000-0000-0000-000000000000'),
        'slug': 'tenant-default',
        'display_name': 'Tenant Default',
        'primary_domain': 'tenant-default.iabank.local',
        'status': Tenant.Status.PILOT,
        'pii_policy_version': 'v1',
    },
    {
        'id': UUID('00000000-0000-0000-0000-000000000001'),
        'slug': 'tenant-alfa',
        'display_name': 'Tenant Alfa',
        'primary_domain': 'tenant-alfa.iabank.local',
        'status': Tenant.Status.PRODUCTION,
        'pii_policy_version': 'v1',
    },
    {
        'id': UUID('00000000-0000-0000-0000-000000000002'),
        'slug': 'tenant-beta',
        'display_name': 'Tenant Beta',
        'primary_domain': 'tenant-beta.iabank.local',
        'status': Tenant.Status.PILOT,
        'pii_policy_version': 'v1',
    },
]


class Command(BaseCommand):
    help = 'Popula tenants e tokens demo usados na fundação frontend.'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recria tokens e redefine default_theme mesmo que já existam registros.',
        )

    def handle(self, *args, **options) -> None:
        force: bool = options.get('force', False)

        if not CACHE_DIR.exists():
            self.stderr.write(
                self.style.WARNING(f'Cache de tokens não encontrado em {CACHE_DIR}. Pulando sincronização.'),
            )
            return

        with transaction.atomic():
            for tenant_data in DEMO_TENANTS:
                tenant = self._ensure_tenant(tenant_data)
                self._sync_tokens(tenant, force=force)

    def _ensure_tenant(self, data: dict[str, Any]) -> Tenant:
        tenant, created = Tenant.objects.update_or_create(
            id=data['id'],
            defaults={
                'slug': data['slug'],
                'display_name': data['display_name'],
                'primary_domain': data['primary_domain'],
                'status': data['status'],
                'pii_policy_version': data['pii_policy_version'],
            },
        )

        action = 'Criado' if created else 'Atualizado'
        self.stdout.write(self.style.SUCCESS(f'{action} tenant {tenant.slug} ({tenant.id})'))
        return tenant

    def _sync_tokens(self, tenant: Tenant, force: bool) -> None:
        cache_file = CACHE_DIR / f'{tenant.id}.json'
        if not cache_file.exists():
            self.stderr.write(
                self.style.WARNING(f'Arquivo de cache não encontrado para {tenant.slug}: {cache_file}'),
            )
            return

        payload = json.loads(cache_file.read_text(encoding='utf-8'))
        schema = payload.get('payload', {})
        version = schema.get('version', '0.0.0')
        categories: dict[str, dict[str, Any]] = schema.get('categories', {})
        wcag_report: dict[str, Any] = schema.get('wcagReport', {})

        foundation_token: TenantThemeToken | None = None
        updated_at = timezone.now()

        for category, tokens in categories.items():
            if not isinstance(tokens, dict):
                self.stderr.write(
                    self.style.WARNING(f'Categoria {category} inválida para {tenant.slug}, ignorando.'),
                )
                continue

            defaults: dict[str, Any] = {
                'json_payload': tokens,
                'wcag_report': wcag_report.get(category),
                'is_default': category == TenantThemeToken.Category.FOUNDATION,
                'version': version,
                'updated_at': updated_at,
            }

            if defaults['is_default']:
                foundation_token = self._upsert_token(tenant, category, defaults, force=force)
            else:
                self._upsert_token(tenant, category, defaults, force=force)

        if foundation_token:
            Tenant.objects.filter(id=tenant.id).update(default_theme=foundation_token)

    def _upsert_token(
        self,
        tenant: Tenant,
        category: str,
        defaults: dict[str, Any],
        force: bool,
    ) -> TenantThemeToken | None:
        manager = TenantThemeToken.objects.unscoped()

        existing = manager.filter(tenant_id=tenant.id, category=category).first()
        if existing and not force:
            self.stdout.write(f'Token {category} já existe para {tenant.slug}, mantendo registro atual.')
            return existing

        token, created = manager.update_or_create(
            tenant_id=tenant.id,
            category=category,
            defaults=defaults,
        )

        action = 'Criado' if created else 'Atualizado'
        self.stdout.write(f'{action} token {category} para {tenant.slug}')
        return token
