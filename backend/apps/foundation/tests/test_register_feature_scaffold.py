from __future__ import annotations

import uuid

import pytest
from django.core.cache import cache
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
        cache.clear()
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
        assert 'ETag' in response

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
        body = response.json()
        assert body['title'] == 'idempotency_key_required'
        assert body['type'].endswith('/idempotency-key')
        assert body['status'] == status.HTTP_400_BAD_REQUEST

    def test_returns_problem_details_when_payload_invalid(self) -> None:
        tenant_id = str(self.tenant.id)
        idempotency_key = '00000000-0000-4000-8000-000000009999'
        response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data={'featureSlug': 'loan-tracking'},  # campos obrigatórios ausentes
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_IDEMPOTENCY_KEY': idempotency_key,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        body = response.json()
        assert body['title'] == 'invalid_request'
        assert body['type'] == 'https://iabank.local/problems/foundation/validation'
        assert isinstance(body.get('invalidParams'), list)
        assert body['status'] == status.HTTP_400_BAD_REQUEST

    def test_returns_problem_details_when_tenant_not_found(self) -> None:
        payload = build_payload()
        missing_tenant = str(uuid.uuid4())
        idempotency_key = '00000000-0000-4000-8000-000000000321'

        response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': missing_tenant}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': missing_tenant,
                'HTTP_IDEMPOTENCY_KEY': idempotency_key,
                'HTTP_TRACEPARENT': '00-cccccccccccccccccccccccccccccccc-dddddddddddddddd-01',
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        body = response.json()
        assert body['title'] == 'tenant_not_found'
        assert body['type'] == 'https://iabank.local/problems/foundation/tenant'

    def test_records_sc001_metric(self, monkeypatch: pytest.MonkeyPatch) -> None:
        payload = build_payload()
        tenant_id = str(self.tenant.id)
        idempotency_key = '00000000-0000-4000-8000-000000000123'

        recorded: list[tuple[str, str, float]] = []

        def fake_record(tenant_slug: str, feature_slug: str, duration_minutes: float) -> None:
            recorded.append((tenant_slug, feature_slug, duration_minutes))

        monkeypatch.setattr(
            'backend.apps.foundation.services.scaffold_registrar.record_scaffolding_duration',
            fake_record,
        )

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
        assert len(recorded) == 1

        tenant_slug, feature_slug, duration_minutes = recorded[0]
        assert tenant_slug == self.tenant.slug
        assert feature_slug == payload['featureSlug']
        expected_minutes = payload['durationMs'] / 60000
        assert duration_minutes == pytest.approx(expected_minutes, rel=1e-3)

    def test_replay_with_same_idempotency_key_returns_existing(self) -> None:
        payload = build_payload()
        tenant_id = str(self.tenant.id)
        idempotency_key = '00000000-0000-4000-8000-000000000456'

        first_response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_IDEMPOTENCY_KEY': idempotency_key,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
            },
        )
        assert first_response.status_code == status.HTTP_201_CREATED

        first_body = first_response.json()

        second_response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_IDEMPOTENCY_KEY': idempotency_key,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
            },
        )

        assert second_response.status_code == status.HTTP_200_OK
        assert second_response['Idempotency-Key'] == idempotency_key
        assert 'ETag' in second_response
        second_body = second_response.json()
        assert second_body['scaffoldId'] == first_body['scaffoldId']

    def test_rejects_different_idempotency_key_within_ttl_window(self) -> None:
        payload = build_payload()
        tenant_id = str(self.tenant.id)
        original_key = '00000000-0000-4000-8000-000000000789'
        conflicting_key = '00000000-0000-4000-8000-000000000790'

        initial_response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_IDEMPOTENCY_KEY': original_key,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
            },
        )
        assert initial_response.status_code == status.HTTP_201_CREATED

        conflict_response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_IDEMPOTENCY_KEY': conflicting_key,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
            },
        )

        assert conflict_response.status_code == status.HTTP_409_CONFLICT
        body = conflict_response.json()
        assert body['title'] == 'idempotency_conflict'
        assert body['type'].endswith('/idempotency-replay')
        assert body['status'] == status.HTTP_409_CONFLICT

    def test_if_none_match_returns_not_modified_when_etag_matches(self) -> None:
        payload = build_payload()
        tenant_id = str(self.tenant.id)
        idempotency_key = '00000000-0000-4000-8000-000000000888'

        first_response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_IDEMPOTENCY_KEY': idempotency_key,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
            },
        )
        assert first_response.status_code == status.HTTP_201_CREATED
        etag = first_response['ETag']

        replay_response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_IDEMPOTENCY_KEY': idempotency_key,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
                'HTTP_IF_NONE_MATCH': etag,
            },
        )

        assert replay_response.status_code == status.HTTP_304_NOT_MODIFIED
        assert replay_response['ETag'] == etag
        assert replay_response['Idempotency-Key'] == idempotency_key

    def test_if_none_match_star_blocks_when_registration_exists(self) -> None:
        payload = build_payload()
        tenant_id = str(self.tenant.id)
        idempotency_key = '00000000-0000-4000-8000-000000000889'

        first_response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_IDEMPOTENCY_KEY': idempotency_key,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
            },
        )
        assert first_response.status_code == status.HTTP_201_CREATED

        second_response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_IDEMPOTENCY_KEY': idempotency_key,
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
                'HTTP_IF_NONE_MATCH': '*',
            },
        )

        assert second_response.status_code == status.HTTP_412_PRECONDITION_FAILED
        assert second_response['ETag'] == first_response['ETag']

    def test_rate_limit_enforced_after_thirty_requests(self) -> None:
        tenant_id = str(self.tenant.id)

        for idx in range(30):
            payload = build_payload()
            payload['featureSlug'] = f'loan-tracking-{idx}'
            response = self.client.post(
                reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
                data=payload,
                format='json',
                **{
                    'HTTP_X_TENANT_ID': tenant_id,
                    'HTTP_IDEMPOTENCY_KEY': f'00000000-0000-4000-8000-{idx:012d}',
                    'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
                },
            )
            assert response.status_code == status.HTTP_201_CREATED

        payload = build_payload()
        payload['featureSlug'] = 'loan-tracking-limit'
        limited_response = self.client.post(
            reverse(API_PATH_NAME, kwargs={'tenant_id': tenant_id}),
            data=payload,
            format='json',
            **{
                'HTTP_X_TENANT_ID': tenant_id,
                'HTTP_IDEMPOTENCY_KEY': '00000000-0000-4000-8000-999999999999',
                'HTTP_TRACEPARENT': '00-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa-bbbbbbbbbbbbbbbb-01',
            },
        )

        assert limited_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert limited_response['Retry-After'] == '60'
