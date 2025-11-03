from __future__ import annotations

from django.test import TestCase
from rest_framework import serializers

from backend.apps.foundation.serializers import TenantThemeSerializer
from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import Tenant, TenantThemeToken


class TenantThemeSerializerSchemaTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        super().setUp()
        self.tenant = Tenant.objects.create(
            slug='tenant-beta',
            display_name='Tenant Beta',
            primary_domain='beta.iabank.test',
            status='pilot',
            pii_policy_version='1.0.0',
        )

    def _serializer_payload(self) -> TenantThemeSerializer:
        with use_tenant(self.tenant.id):
            foundation = TenantThemeToken.objects.create(
                version='1.0.0',
                category=TenantThemeToken.Category.FOUNDATION,
                json_payload={'color.brand.primary': '#1E3A8A'},
                is_default=True,
            )
            semantic = TenantThemeToken.objects.create(
                version='1.0.0',
                category=TenantThemeToken.Category.SEMANTIC,
                json_payload={'surface.background': '#ffffff'},
                wcag_report={'status': 'pass', 'violations': []},
                is_default=True,
            )

        tokens = [foundation, semantic]
        return TenantThemeSerializer(instance={'tenant': self.tenant, 'tokens': tokens})

    def test_serializer_returns_valid_payload(self) -> None:
        serializer = self._serializer_payload()
        data = serializer.data

        self.assertEqual(data['tenantId'], str(self.tenant.id))
        self.assertIn('foundation', data['categories'])
        self.assertEqual(data['categories']['semantic']['surface.background'], '#ffffff')

    def test_serializer_raises_when_token_schema_invalid(self) -> None:
        with use_tenant(self.tenant.id):
            TenantThemeToken.objects.create(
                version='1.0.0',
                category=TenantThemeToken.Category.FOUNDATION,
                json_payload={'color.brand.primary': '#1E3A8A'},
                is_default=True,
            )
            invalid = TenantThemeToken.objects.create(
                version='1.0.0',
                category=TenantThemeToken.Category.COMPONENT,
                json_payload={'button.primary.bg': ''},
                wcag_report={'status': 'pass', 'violations': []},
                is_default=True,
            )

        serializer = TenantThemeSerializer(instance={'tenant': self.tenant, 'tokens': [invalid]})

        with self.assertRaises(serializers.ValidationError):
            _ = serializer.data
