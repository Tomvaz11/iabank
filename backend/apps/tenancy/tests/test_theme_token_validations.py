from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import TestCase

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import Tenant, TenantThemeToken


class TenantThemeTokenValidationTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        super().setUp()
        self.tenant = Tenant.objects.create(
            slug='tenant-alfa',
            display_name='Tenant Alfa',
            primary_domain='alfa.iabank.test',
            status='pilot',
            pii_policy_version='1.0.0',
        )

    def test_requires_wcag_report_for_non_foundation_category(self) -> None:
        with use_tenant(self.tenant.id):
            token = TenantThemeToken(
                version='1.0.0',
                category=TenantThemeToken.Category.SEMANTIC,
                json_payload={'surface.background': '#fff'},
                is_default=False,
            )
            token.tenant = self.tenant

            with self.assertRaises(ValidationError) as exc:
                token.full_clean()

        self.assertIn('wcag_report', exc.exception.message_dict)

    def test_allows_missing_wcag_report_for_foundation_category(self) -> None:
        with use_tenant(self.tenant.id):
            token = TenantThemeToken(
                version='1.0.0',
                category=TenantThemeToken.Category.FOUNDATION,
                json_payload={'color.brand.primary': '#1E3A8A'},
                is_default=True,
            )
            token.tenant = self.tenant

            # Não deve levantar erro de validação.
            token.full_clean()

    def test_prevents_default_when_wcag_status_is_not_pass(self) -> None:
        with use_tenant(self.tenant.id):
            token = TenantThemeToken(
                version='1.0.0',
                category=TenantThemeToken.Category.SEMANTIC,
                json_payload={'surface.background': '#ffffff'},
                wcag_report={'status': 'fail', 'violations': []},
                is_default=True,
            )
            token.tenant = self.tenant

            with self.assertRaises(ValidationError) as exc:
                token.full_clean()

        self.assertIn('wcag_report', exc.exception.message_dict)

    def test_prevents_default_when_wcag_has_violations(self) -> None:
        with use_tenant(self.tenant.id):
            token = TenantThemeToken(
                version='1.0.0',
                category=TenantThemeToken.Category.COMPONENT,
                json_payload={'button.primary.bg': '#1E3A8A'},
                wcag_report={'status': 'pass', 'violations': [{'id': 'color-contrast'}]},
                is_default=True,
            )
            token.tenant = self.tenant

            with self.assertRaises(ValidationError) as exc:
                token.full_clean()

        self.assertIn('wcag_report', exc.exception.message_dict)

    def test_allows_default_when_wcag_pass_without_violations(self) -> None:
        with use_tenant(self.tenant.id):
            token = TenantThemeToken(
                version='1.0.0',
                category=TenantThemeToken.Category.COMPONENT,
                json_payload={'button.primary.bg': '#1E3A8A'},
                wcag_report={'status': 'pass', 'violations': []},
                is_default=True,
            )
            token.tenant = self.tenant

            token.full_clean()
