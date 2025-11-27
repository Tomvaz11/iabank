from __future__ import annotations

import os
from http import HTTPStatus

from django.test import SimpleTestCase

from backend.apps.tenancy.services.seed_preflight import (
    ProblemDetail,
    PreflightContext,
    SeedPreflightConfig,
    SeedPreflightService,
)


class SeedPreflightServiceTest(SimpleTestCase):
    def setUp(self) -> None:
        self.config = SeedPreflightConfig(
            vault_transit_path='transit/seeds/staging/tenant-a/ff3',
            worm_bucket='worm-seeds',
            worm_role_arn='arn:aws:iam::123456789012:role/worm',
            worm_kms_key_id='arn:aws:kms:us-east-1:123456789012:key/seeds',
            worm_retention_days=365,
            allowed_roles={'seed-runner', 'seed-admin'},
            allowed_environments={'dev', 'homolog', 'staging', 'perf'},
        )

    def _context(self, **overrides) -> PreflightContext:
        base: dict[str, object] = {
            'tenant_id': 'tenant-a',
            'environment': 'staging',
            'manifest_path': 'configs/seed_profiles/staging/tenant-a.yaml',
            'requested_by': 'svc:seed-runner',
            'roles': ['seed-runner'],
            'dry_run': False,
        }
        base.update(overrides)
        return PreflightContext(**base)  # type: ignore[arg-type]

    def test_allows_when_dependencies_available_and_role_valid(self) -> None:
        service = SeedPreflightService(config=self.config)
        context = self._context()

        result = service.check(context)

        self.assertTrue(result.allowed)
        self.assertIsNone(result.problem)
        self.assertEqual(result.audit['environment'], 'staging')
        self.assertEqual(result.audit['vault']['available'], True)
        self.assertEqual(result.audit['worm']['available'], True)
        self.assertNotEqual(result.audit['manifest_fingerprint'], context.manifest_path)

    def test_blocks_when_worm_is_missing_on_non_dry_run(self) -> None:
        config = SeedPreflightConfig(
            vault_transit_path='transit/seeds/staging/tenant-a/ff3',
            worm_bucket='',
            worm_role_arn='',
            worm_kms_key_id='',
            worm_retention_days=100,
            allowed_roles={'seed-runner', 'seed-admin'},
            allowed_environments={'staging'},
        )
        service = SeedPreflightService(config=config)
        context = self._context()

        result = service.check(context)

        assert result.problem
        self.assertFalse(result.allowed)
        self.assertEqual(result.problem.status, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertIn('WORM', result.problem.title)
        self.assertEqual(result.problem.type, 'https://iabank.local/problems/seed/worm-unavailable')
        self.assertEqual(result.audit['worm']['available'], False)

    def test_forbids_when_role_not_authorized(self) -> None:
        service = SeedPreflightService(config=self.config)
        context = self._context(roles=['seed-read'])

        result = service.check(context)

        assert result.problem
        self.assertFalse(result.allowed)
        self.assertEqual(result.problem.status, HTTPStatus.FORBIDDEN)
        self.assertEqual(result.problem.title, 'seed_preflight_forbidden')
        self.assertEqual(result.problem.type, 'https://iabank.local/problems/seed/preflight-forbidden')
        self.assertEqual(result.audit['roles'], ['seed-read'])

    def test_skips_worm_validation_on_dry_run(self) -> None:
        config = SeedPreflightConfig(
            vault_transit_path='transit/seeds/staging/tenant-a/ff3',
            worm_bucket='',
            worm_role_arn='',
            worm_kms_key_id='',
            worm_retention_days=0,
            allowed_roles={'seed-runner'},
            allowed_environments={'staging'},
        )
        service = SeedPreflightService(config=config)
        context = self._context(dry_run=True)

        result = service.check(context)

        self.assertTrue(result.allowed)
        self.assertIsNone(result.problem)
        self.assertEqual(result.audit['worm']['skipped_for_dry_run'], True)

    def test_blocks_when_vault_unavailable(self) -> None:
        config = SeedPreflightConfig(
            vault_transit_path='',
            worm_bucket='worm-seeds',
            worm_role_arn='arn:aws:iam::123456789012:role/worm',
            worm_kms_key_id='arn:aws:kms:us-east-1:123456789012:key/seeds',
            worm_retention_days=365,
            allowed_roles={'seed-runner'},
            allowed_environments={'staging'},
        )
        service = SeedPreflightService(config=config)
        context = self._context()

        result = service.check(context)

        assert result.problem
        self.assertFalse(result.allowed)
        self.assertEqual(result.problem.title, 'vault_unavailable')
        self.assertEqual(result.problem.status, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertFalse(result.audit['vault']['available'])

    def test_forbids_environment_not_allowed(self) -> None:
        service = SeedPreflightService(config=self.config)
        context = self._context(environment='prod')

        result = service.check(context)

        assert result.problem
        self.assertFalse(result.allowed)
        self.assertEqual(result.problem.status, HTTPStatus.FORBIDDEN)
        self.assertEqual(result.problem.title, 'seed_preflight_forbidden')

    def test_blocks_when_retention_below_minimum(self) -> None:
        config = SeedPreflightConfig(
            vault_transit_path='transit/seeds/staging/tenant-a/ff3',
            worm_bucket='worm-seeds',
            worm_role_arn='arn:aws:iam::123456789012:role/worm',
            worm_kms_key_id='arn:aws:kms:us-east-1:123456789012:key/seeds',
            worm_retention_days=120,
            allowed_roles={'seed-runner'},
            allowed_environments={'staging'},
        )
        service = SeedPreflightService(config=config, min_worm_retention_days=365)
        context = self._context()

        result = service.check(context)

        assert result.problem
        self.assertFalse(result.allowed)
        self.assertIn('Retencao WORM abaixo do minimo', result.problem.detail)

    def test_enforces_worm_on_dry_run_when_flag_enabled(self) -> None:
        config = SeedPreflightConfig(
            vault_transit_path='transit/seeds/staging/tenant-a/ff3',
            worm_bucket='',
            worm_role_arn='',
            worm_kms_key_id='',
            worm_retention_days=365,
            allowed_roles={'seed-runner'},
            allowed_environments={'staging'},
            enforce_worm_on_dry_run=True,
        )
        service = SeedPreflightService(config=config)
        context = self._context(dry_run=True)

        result = service.check(context)

        assert result.problem
        self.assertFalse(result.allowed)
        self.assertEqual(result.problem.status, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertFalse(result.audit['worm']['available'])
        self.assertFalse(result.audit['worm']['skipped_for_dry_run'])

    def test_config_from_env_and_problem_dict(self) -> None:
        envs = {
            'VAULT_TRANSIT_PATH': 'transit/env',
            'SEEDS_WORM_BUCKET': 'worm-env',
            'SEEDS_WORM_ROLE_ARN': 'arn:role/env',
            'SEEDS_WORM_KMS_KEY_ID': 'arn:kms/env',
            'SEEDS_WORM_RETENTION_DAYS': '365',
            'SEED_ALLOWED_ROLES': 'seed-runner,seed-admin',
            'SEED_ALLOWED_ENVIRONMENTS': 'dev,staging',
            'SEED_ENFORCE_WORM_ON_DRY_RUN': 'true',
        }
        for key, value in envs.items():
            os.environ[key] = value

        cfg = SeedPreflightConfig.from_env()
        self.assertEqual(cfg.vault_transit_path, 'transit/env')
        self.assertIn('seed-runner', cfg.allowed_roles)
        self.assertIn('staging', cfg.allowed_environments)
        self.assertTrue(cfg.enforce_worm_on_dry_run)

        problem = ProblemDetail(
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            title='example',
            detail='detail',
            type='https://iabank.local/problems/example',
        )
        self.assertEqual(
            problem.as_dict(),
            {
                'status': HTTPStatus.SERVICE_UNAVAILABLE,
                'title': 'example',
                'detail': 'detail',
                'type': 'https://iabank.local/problems/example',
            },
        )
        self.assertEqual(SeedPreflightService()._fingerprint(""), "")

        for key in envs:
            os.environ.pop(key, None)
