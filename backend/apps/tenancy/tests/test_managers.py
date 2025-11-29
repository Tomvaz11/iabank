from django.db import connection
from django.test import TestCase

from backend.apps.tenancy.managers import TenantContextError
from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import Tenant
from backend.apps.tenancy.models import TenantThemeToken


class TenantManagerTest(TestCase):
    databases = {"default"}

    def setUp(self) -> None:
        super().setUp()
        self.tenant = Tenant.objects.create(
            slug="tenant-alfa",
            display_name="Tenant Alfa",
            primary_domain="alfa.iabank.test",
            status="pilot",
            pii_policy_version="1.0.0",
        )
        self.other_tenant = Tenant.objects.create(
            slug="tenant-beta",
            display_name="Tenant Beta",
            primary_domain="beta.iabank.test",
            status="pilot",
            pii_policy_version="1.0.0",
        )

    def test_injects_tenant_id_on_create(self) -> None:
        with use_tenant(self.tenant.id):
            created = TenantThemeToken.objects.create(
                version="1.0.0",
                category="foundation",
                json_payload={"primary": "#000"},
                is_default=True,
            )

        self.assertEqual(created.tenant_id, self.tenant.id)
        self.assertEqual(created.json_payload, {"primary": "#000"})

    def test_stores_payload_encrypted_at_rest(self) -> None:
        with use_tenant(self.tenant.id):
            TenantThemeToken.objects.create(
                version="1.0.0",
                category="foundation",
                json_payload={"primary": "#000"},
                is_default=True,
            )

        with connection.cursor() as cursor:
            cursor.execute("SELECT json_payload FROM tenant_theme_tokens LIMIT 1")
            row = cursor.fetchone()

        self.assertIsNotNone(row, 'Registro criptografado deve existir no banco')
        stored_value = row[0]

        self.assertIsInstance(stored_value, (bytes, memoryview))
        self.assertNotIn(b'"primary"', bytes(stored_value))

    def test_filters_queryset_by_active_tenant(self) -> None:
        with use_tenant(self.tenant.id):
            TenantThemeToken.objects.create(
                version="1.0.0",
                category="foundation",
                json_payload={"primary": "#111"},
                is_default=True,
            )

        with use_tenant(self.other_tenant.id):
            TenantThemeToken.objects.create(
                version="1.0.0",
                category="foundation",
                json_payload={"primary": "#222"},
                is_default=True,
            )

            tokens = list(TenantThemeToken.objects.all())

        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].tenant_id, self.other_tenant.id)

    def test_raises_error_when_context_is_missing(self) -> None:
        with self.assertRaises(TenantContextError):
            list(TenantThemeToken.objects.all())

    def test_sets_tenant_guc_for_rls(self) -> None:
        with use_tenant(self.tenant.id):
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_setting('iabank.current_tenant_id', true)")
                value = cursor.fetchone()[0]

        self.assertEqual(str(self.tenant.id), value)
