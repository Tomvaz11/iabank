from __future__ import annotations

from django.test import TestCase
from rest_framework.test import APIClient

from backend.apps.tenancy.models import Tenant
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest, compute_manifest_hash


class SeedProfileValidateAPITest(TestCase):
    databases = {"default"}

    def setUp(self) -> None:
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            slug='tenant-a',
            display_name='Tenant A',
            primary_domain='tenant-a.iabank.test',
            status=Tenant.Status.PILOT,
            pii_policy_version='1.0.0',
        )

    def _headers(self, *, idempotency_key: str, environment: str = 'staging') -> dict[str, str]:
        return {
            'HTTP_X_TENANT_ID': self.tenant.slug,
            'HTTP_X_ENVIRONMENT': environment,
            'HTTP_IDEMPOTENCY_KEY': idempotency_key,
        }

    def _assert_rate_limit_headers(self, response) -> None:
        for header in ('RateLimit-Limit', 'RateLimit-Remaining', 'RateLimit-Reset'):
            self.assertIn(header, response.headers)
            self.assertNotEqual(
                str(response.headers[header]).strip(),
                '',
                f'O header {header} deve ser retornado para governança de RateLimit-*.',
            )

    def test_accepts_valid_manifest_and_returns_caps(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')

        response = self.client.post(
            '/api/v1/seed-profiles/validate',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='validate-1', environment='staging'),
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body.get('valid'))
        self.assertEqual(body.get('issues'), [])
        self.assertEqual(body.get('normalized_version'), manifest['metadata']['version'])
        self.assertIsInstance(body.get('caps'), dict)
        self.assertIn('customers', body.get('caps', {}))
        self._assert_rate_limit_headers(response)
        self.assertIn('Retry-After', response.headers)

    def test_returns_problem_details_for_invalid_manifest(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')
        manifest.pop('volumetry')
        manifest['integrity']['manifest_hash'] = compute_manifest_hash(manifest)

        response = self.client.post(
            '/api/v1/seed-profiles/validate',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='validate-invalid', environment='staging'),
        )

        self.assertEqual(response.status_code, 422)
        problem = response.json()
        self.assertEqual(problem.get('status'), 422)
        violations = problem.get('violations', [])
        self.assertTrue(
            any('volumetry' in v.get('field', '') or 'volumetry' in v.get('message', '') for v in violations),
            '422 deve retornar Problem Details com a lista de violações do manifesto.',
        )
        self._assert_rate_limit_headers(response)

    def test_applies_rate_limit_and_returns_retry_after(self) -> None:
        manifest = build_manifest(
            tenant_slug=self.tenant.slug,
            environment='staging',
            overrides={'rate_limit': {'limit': 1, 'window_seconds': 60}},
        )

        first = self.client.post(
            '/api/v1/seed-profiles/validate',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='rate-limit-1', environment='staging'),
        )
        self.assertEqual(first.status_code, 200, 'Primeira chamada deve ser aceita para validar o manifesto.')

        second = self.client.post(
            '/api/v1/seed-profiles/validate',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='rate-limit-2', environment='staging'),
        )

        self.assertEqual(second.status_code, 429)
        problem = second.json()
        self.assertEqual(problem.get('status'), 429)
        self.assertIn('Retry-After', second.headers)
        self.assertIn('rate', problem.get('title', '').lower())
        self._assert_rate_limit_headers(second)
