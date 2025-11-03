from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
import uuid
from rest_framework.test import APITestCase

from backend.apps.foundation.models import FeatureTemplateRegistration, FeatureTemplateMetric
from backend.apps.tenancy.models import Tenant


class ListTenantSuccessMetricsApiTest(APITestCase):
    databases = {'default'}

    def setUp(self) -> None:
        super().setUp()
        self.tenant = Tenant.objects.create(
            slug='tenant-alfa',
            display_name='Tenant Alfa',
            primary_domain='tenant-alfa.iabank.test',
            status='pilot',
            pii_policy_version='1.0.0',
        )
        self.registration = FeatureTemplateRegistration.objects.create(
            tenant=self.tenant,
            feature_slug='loan-tracking',
            slice=FeatureTemplateRegistration.Slice.FEATURES,
            status=FeatureTemplateRegistration.Status.TESTED,
            scaffold_manifest=[{'slice': 'features', 'files': []}],
            lint_commit_hash='1234567890abcdef1234567890abcdef12345678',
            sc_references=['@SC-001', '@SC-003'],
            metadata={'cliVersion': '0.1.0'},
            created_by=self.tenant.id,
            duration_ms=120000,
            idempotency_key='00000000-0000-4000-8000-000000000001',
        )

        now = timezone.now()
        FeatureTemplateMetric.objects.bulk_create(
            [
                FeatureTemplateMetric(
                    tenant=self.tenant,
                    registration=self.registration,
                    metric_code=FeatureTemplateMetric.MetricCode.SC_001,
                    value=Decimal('42.5'),
                    collected_at=now,
                    source=FeatureTemplateMetric.Source.CI,
                ),
                FeatureTemplateMetric(
                    tenant=self.tenant,
                    registration=self.registration,
                    metric_code=FeatureTemplateMetric.MetricCode.SC_002,
                    value=Decimal('96.7'),
                    collected_at=now - timedelta(hours=1),
                    source=FeatureTemplateMetric.Source.CHROMATIC,
                ),
                FeatureTemplateMetric(
                    tenant=self.tenant,
                    registration=self.registration,
                    metric_code=FeatureTemplateMetric.MetricCode.SC_003,
                    value=Decimal('1'),
                    collected_at=now - timedelta(days=1),
                    source=FeatureTemplateMetric.Source.MANUAL,
                ),
            ]
        )

    def _url(self) -> str:
        return reverse(
            'foundation:list-tenant-success-metrics',
            kwargs={'tenant_id': str(self.tenant.id)},
        )

    def test_returns_paginated_metrics_with_rate_limit_headers(self) -> None:
        response = self.client.get(
            self._url(),
            data={'page': 1, 'page_size': 2},
            **{
                'HTTP_X_TENANT_ID': str(self.tenant.id),
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('RateLimit-Limit', response)
        self.assertIn('RateLimit-Remaining', response)
        self.assertIn('RateLimit-Reset', response)

        payload = response.json()
        self.assertEqual(payload['pagination']['page'], 1)
        self.assertEqual(payload['pagination']['perPage'], 2)
        self.assertEqual(payload['pagination']['totalItems'], 3)
        self.assertEqual(payload['pagination']['totalPages'], 2)

        self.assertEqual(len(payload['data']), 2)
        first_metric = payload['data'][0]
        self.assertEqual(first_metric['code'], 'SC-001')
        self.assertEqual(first_metric['source'], 'ci')
        self.assertIsInstance(first_metric['value'], (int, float))
        self.assertIn('collectedAt', first_metric)

    def test_requires_matching_tenant_header(self) -> None:
        # Gerar um UUID válido e garantidamente diferente do tenant_id
        mismatched_tenant = str(uuid.uuid4())
        response = self.client.get(
            self._url(),
            data={'page': 1, 'page_size': 2},
            **{
                'HTTP_X_TENANT_ID': mismatched_tenant,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-02',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()['errors']['X-Tenant-Id'][0],
            'Cabeçalho X-Tenant-Id inválido ou ausente.',
        )

    def test_handles_empty_dataset(self) -> None:
        FeatureTemplateMetric.objects.filter(tenant=self.tenant).delete()

        response = self.client.get(
            self._url(),
            data={'page': 1, 'page_size': 5},
            **{
                'HTTP_X_TENANT_ID': str(self.tenant.id),
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-03',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload['data'], [])
        self.assertEqual(payload['pagination']['totalItems'], 0)
