from __future__ import annotations

import os
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedQueue, SeedRBAC, SeedRun, Tenant
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest


def _set_preflight_env() -> None:
    envs: dict[str, str] = {
        'VAULT_TRANSIT_PATH': 'transit/seeds/staging/tenant-a/ff3',
        'SEEDS_WORM_BUCKET': 'worm-bucket',
        'SEEDS_WORM_ROLE_ARN': 'arn:aws:iam::123:role/worm',
        'SEEDS_WORM_KMS_KEY_ID': 'arn:aws:kms:us-east-1:123:key/worm',
        'SEEDS_WORM_RETENTION_DAYS': '365',
        'SEED_ALLOWED_ENVIRONMENTS': 'dev,homolog,staging,perf',
        'SEED_ALLOWED_ROLES': 'seed-runner,seed-admin',
    }
    os.environ.update(envs)


class SeedRunsAPITest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        _set_preflight_env()
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            slug='tenant-seeds',
            display_name='Tenant Seeds',
            primary_domain='tenant-seeds.iabank.local',
            pii_policy_version='v1',
        )
        with use_tenant(self.tenant.id):
            SeedRBAC.objects.create(
                environment='staging',
                subject='svc-seeds',
                role=SeedRBAC.Role.SEED_RUNNER,
                policy_version='1.0.0',
            )
            SeedRBAC.objects.create(
                environment='staging',
                subject='svc-admin',
                role=SeedRBAC.Role.SEED_ADMIN,
                policy_version='1.0.0',
            )

    def _headers(self, *, idempotency_key: str, environment: str = 'staging', subject: str = 'svc-seeds') -> dict[str, str]:
        return {
            'HTTP_X_TENANT_ID': self.tenant.slug,
            'HTTP_X_ENVIRONMENT': environment,
            'HTTP_IDEMPOTENCY_KEY': idempotency_key,
            'HTTP_X_SEED_SUBJECT': subject,
        }

    def _assert_rate_limit_headers(self, response) -> None:
        for header in ('RateLimit-Limit', 'RateLimit-Remaining', 'RateLimit-Reset', 'Retry-After'):
            self.assertIn(header, response.headers)
            self.assertNotEqual(str(response.headers[header]).strip(), '')

    def test_create_seed_run_returns_etag_and_headers(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')

        response = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest, 'manifest_path': 'configs/seed_profiles/staging/tenant-seeds.yaml'},
            format='json',
            **self._headers(idempotency_key='create-1'),
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertIn('seed_run_id', body)
        self.assertEqual(body.get('status'), SeedRun.Status.QUEUED)
        self.assertEqual(body.get('manifest_hash'), manifest['integrity']['manifest_hash'])
        self.assertIn('ETag', response.headers)
        self._assert_rate_limit_headers(response)

        with use_tenant(self.tenant.id):
            run = SeedRun.objects.filter(id=body['seed_run_id']).first()
            self.assertIsNotNone(run)
            assert run
            self.assertEqual(run.manifest_hash_sha256, manifest['integrity']['manifest_hash'])
            queue_entries = SeedQueue.objects.unscoped().filter(seed_run_id=body['seed_run_id'])
            self.assertGreaterEqual(queue_entries.count(), 1)

    def test_get_seed_run_supports_if_none_match(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')
        created = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='create-304'),
        )
        etag = created.headers.get('ETag', '')
        seed_run_id = created.json()['seed_run_id']

        first_get = self.client.get(
            f'/api/v1/seed-runs/{seed_run_id}',
            **self._headers(idempotency_key='poll-1'),
        )
        self.assertEqual(first_get.status_code, 200)
        self.assertEqual(first_get.headers.get('ETag'), etag)
        self._assert_rate_limit_headers(first_get)

        not_modified = self.client.get(
            f'/api/v1/seed-runs/{seed_run_id}',
            **{
                **self._headers(idempotency_key='poll-2'),
                'HTTP_IF_NONE_MATCH': etag,
            },
        )
        self.assertEqual(not_modified.status_code, 304)
        self._assert_rate_limit_headers(not_modified)

    def test_cancel_seed_run_requires_if_match_and_sets_aborted(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')
        created = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='create-cancel'),
        )
        seed_run_id = created.json()['seed_run_id']
        etag = created.headers['ETag']

        cancel = self.client.post(
            f'/api/v1/seed-runs/{seed_run_id}/cancel',
            {},
            format='json',
            **{
                **self._headers(idempotency_key='cancel-1', subject='svc-admin'),
                'HTTP_IF_MATCH': etag,
            },
        )

        self.assertEqual(cancel.status_code, 202)
        self._assert_rate_limit_headers(cancel)
        with use_tenant(self.tenant.id):
            run = SeedRun.objects.get(id=seed_run_id)
            self.assertEqual(run.status, SeedRun.Status.ABORTED)
            self.assertGreater(run.finished_at, timezone.now() - timedelta(minutes=5))

    def test_blocks_request_outside_offpeak_window(self) -> None:
        manifest = build_manifest(
            tenant_slug=self.tenant.slug,
            environment='staging',
            overrides={
                'window': {'start_utc': '10:00', 'end_utc': '10:30'},
            },
        )

        response = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='offpeak-1'),
        )

        self.assertEqual(response.status_code, 403)
        problem = response.json()
        self.assertIn('offpeak_window_closed', problem.get('title', ''))

    def test_retry_after_header_when_queue_busy(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')
        future = timezone.now() + timedelta(minutes=1)
        with use_tenant(self.tenant.id):
            SeedQueue.objects.create(
                tenant_id=self.tenant.id,
                environment='staging',
                status=SeedQueue.Status.PENDING,
                enqueued_at=timezone.now(),
                expires_at=future,
            )

        blocked = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='retry-after'),
        )

        self.assertEqual(blocked.status_code, 429)
        self.assertIn('Retry-After', blocked.headers)
        self.assertNotEqual(str(blocked.headers['Retry-After']).strip(), '')
