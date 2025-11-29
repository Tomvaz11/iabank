from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedIdempotency, Tenant
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest, compute_manifest_hash


class SeedProfileValidateIdempotencyTest(TestCase):
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

    def test_replay_returns_same_response_and_persists_idempotency_entry(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')
        started_at = timezone.now()

        first = self.client.post(
            '/api/v1/seed-profiles/validate',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='idempo-1', environment='staging'),
        )
        self.assertEqual(first.status_code, 200, 'Primeira validação deve ser aceita com manifesto válido.')

        replay = self.client.post(
            '/api/v1/seed-profiles/validate',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='idempo-1', environment='staging'),
        )

        self.assertEqual(replay.status_code, first.status_code)
        self.assertEqual(replay.json(), first.json())
        self._assert_rate_limit_headers(replay)

        with use_tenant(self.tenant.id):
            entries = list(SeedIdempotency.objects.all())

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.environment, manifest['metadata']['environment'])
        self.assertEqual(entry.idempotency_key, 'idempo-1')
        self.assertEqual(entry.manifest_hash_sha256, compute_manifest_hash(manifest))
        expires_in = entry.expires_at - started_at
        self.assertGreaterEqual(expires_in.total_seconds(), 23 * 3600)
        self.assertLessEqual(expires_in.total_seconds(), (24 * 3600) + 120)

    def test_returns_conflict_when_manifest_hash_differs(self) -> None:
        existing_manifest = build_manifest(
            tenant_slug=self.tenant.slug,
            environment='staging',
            overrides={'metadata': {'version': '1.0.0'}},
        )
        incoming_manifest = build_manifest(
            tenant_slug=self.tenant.slug,
            environment='staging',
            overrides={'metadata': {'version': '2.0.0'}},
        )

        with use_tenant(self.tenant.id):
            SeedIdempotency.objects.create(
                environment='staging',
                idempotency_key='idempo-conflict',
                manifest_hash_sha256=compute_manifest_hash(existing_manifest),
                mode=existing_manifest['mode'],
                expires_at=timezone.now() + timedelta(hours=24),
            )

        response = self.client.post(
            '/api/v1/seed-profiles/validate',
            {'manifest': incoming_manifest},
            format='json',
            **self._headers(idempotency_key='idempo-conflict', environment='staging'),
        )

        self.assertEqual(response.status_code, 409)
        problem = response.json()
        self.assertEqual(problem.get('title'), 'idempotency_conflict')
        self.assertEqual(problem.get('status'), 409)
        self._assert_rate_limit_headers(response)

        with use_tenant(self.tenant.id):
            self.assertEqual(SeedIdempotency.objects.count(), 1)
            self.assertEqual(
                SeedIdempotency.objects.first().manifest_hash_sha256,
                compute_manifest_hash(existing_manifest),
            )
