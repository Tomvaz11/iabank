from django.test import TestCase
from rest_framework.test import APIClient

from backend.apps.tenancy.models import Tenant
from backend.apps.tenancy.models import TenantThemeToken


class TenantRLSEnforcementTest(TestCase):
    databases = {"default"}

    def setUp(self) -> None:
        super().setUp()
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            slug="tenant-alfa",
            display_name="Tenant Alfa",
            primary_domain="alfa.iabank.test",
            status="pilot",
            pii_policy_version="1.0.0",
        )

    def test_rejects_requests_without_tenant_header(self) -> None:
        response = self.client.get(
            "/api/v1/tenants/tenant-alfa/themes/current",
            HTTP_TRACEPARENT="00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-00",
            HTTP_TRACESTATE="tenant-id=tenant-alfa",
        )

        self.assertEqual(
            response.status_code,
            400,
            "A API deve rejeitar requisições sem cabeçalho X-Tenant-Id obrigatório.",
        )

    def test_enforces_row_level_security(self) -> None:
        TenantThemeToken.objects.create(
            tenant_id=self.tenant.id,
            version="1.0.0",
            category="foundation",
            json_payload={"primary": "#000"},
            is_default=True,
        )

        other_tenant = Tenant.objects.create(
            slug="tenant-beta",
            display_name="Tenant Beta",
            primary_domain="beta.iabank.test",
            status="pilot",
            pii_policy_version="1.0.0",
        )

        response = self.client.get(
            f"/api/v1/tenants/{other_tenant.slug}/themes/current",
            HTTP_X_TENANT_ID="tenant-alfa",
            HTTP_TRACEPARENT="00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-00",
            HTTP_TRACESTATE="tenant-id=tenant-alfa",
        )

        self.assertEqual(
            response.status_code,
            404,
            "Requisições com tenant_id divergente devem ser protegidas por RLS.",
        )

    def test_masks_pii_fields_in_logs(self) -> None:
        with self.assertLogs("backend.apps.tenancy", level="INFO") as captured:
            self.client.get(
                f"/api/v1/tenant-metrics/{self.tenant.slug}/sc",
                HTTP_X_TENANT_ID=self.tenant.slug,
                HTTP_TRACEPARENT="00-cccccccccccccccccccccccccccccccc-dddddddddddddddd-00",
                HTTP_TRACESTATE="tenant-id=tenant-alfa",
            )

        joined = " ".join(captured.output)
        self.assertNotIn(self.tenant.primary_domain, joined)
        self.assertIn("***", joined, "Domínio deve ser mascarado nos logs.")
