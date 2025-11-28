from __future__ import annotations

import os
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedIdempotency, SeedRBAC, SeedRun, Tenant
from backend.apps.tenancy.services.seed_idempotency import SeedIdempotencyService
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest


def _set_preflight_env() -> None:
    os.environ.update(
        {
            'VAULT_TRANSIT_PATH': 'transit/seeds/staging/tenant-a/ff3',
            'SEEDS_WORM_BUCKET': 'worm-bucket',
            'SEEDS_WORM_ROLE_ARN': 'arn:aws:iam::123:role/worm',
            'SEEDS_WORM_KMS_KEY_ID': 'arn:aws:kms:us-east-1:123:key/worm',
            'SEEDS_WORM_RETENTION_DAYS': '365',
            'SEED_ALLOWED_ENVIRONMENTS': 'dev,homolog,staging,perf',
            'SEED_ALLOWED_ROLES': 'seed-runner,seed-admin',
        }
    )


class SeedIdempotencyAPITest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        _set_preflight_env()
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            slug='tenant-idempo',
            display_name='Tenant Idempo',
            primary_domain='tenant-idempo.iabank.local',
            pii_policy_version='v1',
        )
        with use_tenant(self.tenant.id):
            SeedRBAC.objects.create(
                environment='staging',
                subject='svc-idempo',
                role=SeedRBAC.Role.SEED_RUNNER,
                policy_version='1.0.0',
            )

    def _headers(self, *, idempotency_key: str, subject: str = 'svc-idempo', environment: str = 'staging') -> dict[str, str]:
        return {
            'HTTP_X_TENANT_ID': self.tenant.slug,
            'HTTP_X_ENVIRONMENT': environment,
            'HTTP_IDEMPOTENCY_KEY': idempotency_key,
            'HTTP_X_SEED_SUBJECT': subject,
        }

    def _assert_single_idempotency_entry(self, key: str) -> SeedIdempotency:
        with use_tenant(self.tenant.id):
            entries = SeedIdempotency.objects.filter(idempotency_key=key)
            self.assertEqual(entries.count(), 1)
            return entries.first()  # type: ignore[return-value]

    def test_replay_returns_same_seed_run(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')
        first = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='idempo-key'),
        )
        first_body = first.json()

        replay = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='idempo-key'),
        )

        self.assertEqual(replay.status_code, first.status_code)
        self.assertEqual(replay.json()['seed_run_id'], first_body['seed_run_id'])
        entry = self._assert_single_idempotency_entry('idempo-key')
        expires_in = entry.expires_at - timezone.now()
        self.assertGreaterEqual(expires_in.total_seconds(), 23 * 3600)
        self.assertLessEqual(expires_in.total_seconds(), (24 * 3600) + 120)
        with use_tenant(self.tenant.id):
            self.assertEqual(SeedRun.objects.count(), 1)

    def test_conflict_when_manifest_hash_differs(self) -> None:
        manifest_a = build_manifest(tenant_slug=self.tenant.slug, environment='staging')
        manifest_b = build_manifest(
            tenant_slug=self.tenant.slug,
            environment='staging',
            overrides={'metadata': {'version': '2.0.0'}},
        )
        self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest_a},
            format='json',
            **self._headers(idempotency_key='conflict-key'),
        )

        conflict = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest_b},
            format='json',
            **self._headers(idempotency_key='conflict-key'),
        )

        self.assertEqual(conflict.status_code, 409)
        problem = conflict.json()
        self.assertEqual(problem.get('title'), 'idempotency_conflict')
        with use_tenant(self.tenant.id):
            self.assertEqual(SeedRun.objects.count(), 1)

    def test_expired_idempotency_entry_allows_new_run(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')
        expired_at = timezone.now() - timedelta(hours=1)
        with use_tenant(self.tenant.id):
            SeedIdempotency.objects.create(
                environment='staging',
                idempotency_key='expired-key',
                manifest_hash_sha256='stale',
                mode='baseline',
                expires_at=expired_at,
            )

        response = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='expired-key'),
        )

        self.assertEqual(response.status_code, 201)
        entry = self._assert_single_idempotency_entry('expired-key')
        self.assertGreater(entry.expires_at, timezone.now())

    def test_replay_without_cached_response_reuses_seed_run(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')
        first = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='idempo-replay'),
        )
        self.assertEqual(first.status_code, 201)
        first_body = first.json()
        SeedIdempotencyService._response_cache.clear()

        replay = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='idempo-replay'),
        )

        self.assertEqual(replay.status_code, 201)
        self.assertEqual(replay.json()['seed_run_id'], first_body['seed_run_id'])
        self._assert_single_idempotency_entry('idempo-replay')
