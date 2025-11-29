from __future__ import annotations

import pytest
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from backend.apps.tenancy.models import Tenant
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest


def _create_tenant() -> Tenant:
    return Tenant.objects.create(
        slug='tenant-auth',
        display_name='Tenant Auth',
        primary_domain='tenant-auth.iabank.local',
        pii_policy_version='v1',
    )


def _set_preflight_env(monkeypatch: pytest.MonkeyPatch) -> None:
    envs: dict[str, str] = {
        'VAULT_TRANSIT_PATH': 'transit/seeds/staging/tenant-auth/ff3',
        'SEEDS_WORM_BUCKET': 'worm-bucket',
        'SEEDS_WORM_ROLE_ARN': 'arn:aws:iam::123:role/worm',
        'SEEDS_WORM_KMS_KEY_ID': 'arn:aws:kms:us-east-1:123:key/worm',
        'SEEDS_WORM_RETENTION_DAYS': '365',
        'SEED_ALLOWED_ENVIRONMENTS': 'dev,homolog,staging,perf',
        'SEED_ALLOWED_ROLES': 'seed-runner,seed-admin',
    }
    for key, value in envs.items():
        monkeypatch.setenv(key, value)


@pytest.mark.django_db
def test_seed_data_cli_rejects_seed_read_role(capfd, monkeypatch: pytest.MonkeyPatch) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)

    with pytest.raises(SystemExit) as excinfo:
        call_command(
            'seed_data',
            tenant_id=str(tenant.id),
            environment='staging',
            mode='baseline',
            roles=['seed-read'],
        )

    err = capfd.readouterr().err
    assert excinfo.value.code == 1
    assert 'seed_preflight_forbidden' in err


class SeedAuthorizationAPITest(TestCase):
    databases = {"default"}

    def setUp(self) -> None:
        self.client = APIClient()
        self.tenant = _create_tenant()

    def _headers(self, *, idempotency_key: str, environment: str) -> dict[str, str]:
        return {
            'HTTP_X_TENANT_ID': self.tenant.slug,
            'HTTP_X_ENVIRONMENT': environment,
            'HTTP_IDEMPOTENCY_KEY': idempotency_key,
        }

    def test_validate_blocks_environment_not_allowed(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='prod')

        response = self.client.post(
            '/api/v1/seed-profiles/validate',
            {'manifest': manifest},
            format='json',
            **self._headers(idempotency_key='forbidden-env', environment='prod'),
        )

        self.assertEqual(response.status_code, 403)
        body = response.json()
        self.assertEqual(body.get('title'), 'environment_not_allowed')
        self.assertIn('environment', body.get('detail', '').lower())
