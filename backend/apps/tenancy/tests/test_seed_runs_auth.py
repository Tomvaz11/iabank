from __future__ import annotations

import os

from django.test import TestCase
from rest_framework.test import APIClient

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedRBAC, SeedRun, Tenant
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest
from backend.apps.tenancy.services.worm_retention import MIN_WORM_RETENTION_DAYS


def _set_preflight_env() -> None:
    os.environ.update(
        {
            'VAULT_TRANSIT_PATH': 'transit/seeds/staging/tenant-a/ff3',
            'SEEDS_WORM_BUCKET': 'worm-bucket',
            'SEEDS_WORM_ROLE_ARN': 'arn:aws:iam::123:role/worm',
            'SEEDS_WORM_KMS_KEY_ID': 'arn:aws:kms:us-east-1:123:key/worm',
            'SEEDS_WORM_RETENTION_DAYS': str(MIN_WORM_RETENTION_DAYS),
            'SEED_ALLOWED_ENVIRONMENTS': 'dev,homolog,staging,perf',
            'SEED_ALLOWED_ROLES': 'seed-runner,seed-admin',
        }
    )


class SeedRunsAuthTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        _set_preflight_env()
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            slug='tenant-rbac',
            display_name='Tenant RBAC',
            primary_domain='tenant-rbac.iabank.local',
            pii_policy_version='v1',
        )
        with use_tenant(self.tenant.id):
            SeedRBAC.objects.create(
                environment='staging',
                subject='svc-runner',
                role=SeedRBAC.Role.SEED_RUNNER,
                policy_version='1.0.0',
            )

    def _headers(self, *, idempotency_key: str, environment: str = 'staging', subject: str = 'svc-runner') -> dict[str, str]:
        return {
            'HTTP_X_TENANT_ID': self.tenant.slug,
            'HTTP_X_ENVIRONMENT': environment,
            'HTTP_IDEMPOTENCY_KEY': idempotency_key,
            'HTTP_X_SEED_SUBJECT': subject,
        }

    def test_create_seed_run_blocks_unauthorized_subject(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')

        response = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='rbac-1', subject='svc-read-only'),
        )

        self.assertEqual(response.status_code, 403)
        problem = response.json()
        self.assertIn('forbidden', problem.get('title', ''))
        with use_tenant(self.tenant.id):
            self.assertEqual(SeedRun.objects.count(), 0)

    def test_cancel_requires_admin_role(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')
        created = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='rbac-2'),
        )
        seed_run_id = created.json()['seed_run_id']

        denied = self.client.post(
            f'/api/v1/seed-runs/{seed_run_id}/cancel',
            {},
            format='json',
            **self._headers(idempotency_key='cancel-denied', subject='svc-runner'),
        )

        self.assertEqual(denied.status_code, 403)
        with use_tenant(self.tenant.id):
            self.assertEqual(SeedRun.objects.get(id=seed_run_id).status, SeedRun.Status.QUEUED)

    def test_blocks_environment_not_bound_in_rbac(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging')
        response = self.client.post(
            '/api/v1/seed-runs',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='rbac-3', environment='perf'),
        )

        self.assertEqual(response.status_code, 403)
        with use_tenant(self.tenant.id):
            self.assertEqual(SeedRun.objects.count(), 0)
