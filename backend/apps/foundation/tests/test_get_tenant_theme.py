from __future__ import annotations

from django.urls import reverse
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APITestCase

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import Tenant, TenantThemeToken


class GetTenantThemeApiTest(APITestCase):
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
        with use_tenant(self.tenant.id):
            TenantThemeToken.objects.create(
                version='1.0.0',
                category=TenantThemeToken.Category.FOUNDATION,
                json_payload={'color.brand.primary': '#1E3A8A'},
                is_default=True,
            )
            TenantThemeToken.objects.create(
                version='1.0.0',
                category=TenantThemeToken.Category.SEMANTIC,
                json_payload={'surface.background': '#ffffff'},
                wcag_report={'contrast': 'AA', 'status': 'pass', 'violations': []},
                is_default=True,
            )

    def _url(self) -> str:
        return reverse('foundation:get-tenant-theme', kwargs={'tenant_id': self.tenant.id})

    def test_returns_tokens_grouped_by_category(self) -> None:
        response = self.client.get(
            self._url(),
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['tenantId'], str(self.tenant.id))
        self.assertEqual(payload['version'], '1.0.0')
        self.assertIn('generatedAt', payload)
        # Valida formato ISO
        self.assertIsNotNone(parse_datetime(payload['generatedAt']))

        categories = payload['categories']
        self.assertIn('foundation', categories)
        self.assertIn('semantic', categories)
        self.assertEqual(categories['foundation']['color.brand.primary'], '#1E3A8A')
        self.assertEqual(categories['semantic']['surface.background'], '#ffffff')

        wcag_report = payload['wcagReport']
        self.assertEqual(wcag_report['semantic']['contrast'], 'AA')

        self.assertIn('ETag', response)
        self.assertTrue(response['ETag'].startswith('"'))

    def test_returns_not_modified_when_if_none_match_matches(self) -> None:
        first = self.client.get(
            self._url(),
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )

        etag = first['ETag']

        second = self.client.get(
            self._url(),
            HTTP_X_TENANT_ID=str(self.tenant.id),
            HTTP_IF_NONE_MATCH=etag,
        )

        self.assertEqual(second.status_code, status.HTTP_304_NOT_MODIFIED)
        self.assertEqual(second['ETag'], etag)

    def test_requires_tenant_header(self) -> None:
        response = self.client.get(self._url())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_not_found_when_no_tokens(self) -> None:
        with use_tenant(self.tenant.id):
            TenantThemeToken.objects.all().delete()

        response = self.client.get(
            self._url(),
            HTTP_X_TENANT_ID=str(self.tenant.id),
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
