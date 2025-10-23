from __future__ import annotations

import uuid

import pytest
from django.apps import apps
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from backend.apps.tenancy.models.tenant import Tenant

API_PATH_NAME = 'foundation:register-feature-scaffold'


def build_payload() -> dict[str, object]:
    return {
        'featureSlug': 'loan-tracking',
        'initiatedBy': str(uuid.uuid4()),
        'slices': [
            {
                'slice': 'app',
                'files': [
                    {
                        'path': 'frontend/src/app/loan-tracking/index.tsx',
                        'checksum': '4a7d1ed414474e4033ac29ccb8653d9b4a7d1ed414474e4033ac29ccb8653d9b',
                    }
                ],
            },
            {
                'slice': 'pages',
                'files': [
                    {
                        'path': 'frontend/src/pages/loan-tracking/index.tsx',
                        'checksum': '6b86b273ff34fce19d6b804eff5a3f5746e0f2c6313be24d09aef7b54afc8cdd',
                    }
                ],
            },
        ],
        'lintCommitHash': '1234567890abcdef1234567890abcdef12345678',
        'scReferences': ['@SC-001', '@SC-003'],
        'durationMs': 1450,
        'metadata': {'cliVersion': '0.1.0'},
    }


@pytest.mark.django_db
class TestRegisterFeatureScaffoldAPI:
    def setup_method(self) -> None:
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            slug='tenant-alfa',
            display_name='Tenant Alfa',
            primary_domain='tenant-alfa.iabank.test',
            pii_policy_version='1.0.0',
        )

    def test_registers_scaffold_and_persists_registration(self) -> None:
        payload = build_payload()
        tenant_id = str(self.tenant.id)
        idempotency_key = '00000000-0000-4000-8000-000000000123'

        response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_IDEMPOTENCY_KEY': idempotency_key,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
                'HTTP_TRACESTATE': f'tenant-id={tenant_id}',
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response['Idempotency-Key'] == idempotency_key
        assert response['Location'].endswith(f'/features/scaffold/{payload["featureSlug"]}')

        body = response.json()
        assert body['tenantId'] == tenant_id
        assert body['status'] == 'initiated'
        uuid.UUID(body['scaffoldId'])  # valida formato UUID

        registration_model = apps.get_model('foundation', 'FeatureTemplateRegistration')
        assert (
            registration_model.objects.filter(
                tenant_id=tenant_id,
                feature_slug=payload['featureSlug'],
            ).count()
            == 1
        )

    def test_rejects_requests_without_idempotency_key(self) -> None:
        payload = build_payload()
        tenant_id = str(self.tenant.id)

        response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Idempotency-Key' in response.json()['errors']
