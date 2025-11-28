from __future__ import annotations

from http import HTTPStatus
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone as dt_timezone

from django.test import TestCase

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import BudgetRateLimit, Tenant
from backend.apps.tenancy.services.budget import BudgetService, BudgetSnapshot
from backend.apps.tenancy.services.seed_runs import ProblemDetail, SeedRunService
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest


class SeedBudgetServiceTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            slug='tenant-budget-service',
            display_name='Tenant Budget',
            primary_domain='tenant-budget.iabank.local',
            pii_policy_version='v1',
        )
        self.service = SeedRunService()

    def test_budget_record_created_on_seed_run_creation(self) -> None:
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging', mode='baseline')

        creation = self.service.create_seed_run(
            tenant_id=self.tenant.id,
            environment='staging',
            manifest=manifest,
            manifest_path='configs/seed_profiles/staging/tenant-budget-service.yaml',
            idempotency_key='budget-1',
            requested_by='svc-budget',
            dry_run=False,
            mode='baseline',
        )

        with use_tenant(self.tenant.id):
            budget = BudgetRateLimit.objects.filter(seed_profile=creation.seed_profile).first()

        self.assertIsNotNone(budget)
        assert budget
        self.assertEqual(budget.rate_limit_limit, manifest['rate_limit']['limit'])
        self.assertEqual(budget.rate_limit_remaining, manifest['rate_limit']['limit'])
        self.assertAlmostEqual(float(budget.budget_cost_cap), 25.0, delta=0.01)
        self.assertEqual(budget.cost_model_version, '2025-01-15')
        self.assertEqual(creation.seed_run.rate_limit_usage.get('limit'), manifest['rate_limit']['limit'])

    def test_environment_gate_blocks_dr_outside_required_envs(self) -> None:
        problem = self.service.ensure_environment_gate(environment='dev', mode='dr')
        self.assertIsInstance(problem, ProblemDetail)
        assert problem
        self.assertEqual(problem.status, HTTPStatus.FORBIDDEN)
        self.assertIn('staging', problem.detail)

        allowed = self.service.ensure_environment_gate(environment='staging', mode='dr')
        self.assertIsNone(allowed)

    def test_cost_model_version_mismatch_returns_problem(self) -> None:
        manifest = build_manifest(
            tenant_slug=self.tenant.slug,
            environment='staging',
            mode='carga',
            overrides={'budget': {'cost_model_version': '2099-01-01'}},
        )

        problem = self.service.ensure_cost_model_alignment(manifest=manifest)

        self.assertIsInstance(problem, ProblemDetail)
        assert problem
        self.assertEqual(problem.status, HTTPStatus.UNPROCESSABLE_ENTITY)
        self.assertIn('cost_model', problem.title)

    def test_missing_worm_evidence_blocks_carga(self) -> None:
        manifest = build_manifest(
            tenant_slug=self.tenant.slug,
            environment='staging',
            mode='carga',
            overrides={'integrity': {'worm_proof': ''}},
        )

        problem = self.service.ensure_worm_evidence(manifest=manifest, mode='carga')

        self.assertIsInstance(problem, ProblemDetail)
        assert problem
        self.assertEqual(problem.status, HTTPStatus.FORBIDDEN)
        self.assertIn('WORM', problem.detail)

    def test_cost_model_missing_file_raises_runtime_error(self) -> None:
        missing = Path(tempfile.gettempdir()) / 'cost-model-missing.json'
        if missing.exists():
            missing.unlink()

        with self.assertRaises(RuntimeError):
            BudgetService(cost_model_path=missing)

    def test_cost_model_missing_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'cost-model-invalid.yaml'
            path.write_text('schema_version: v1\nmodes: {}\n', encoding='utf-8')

            with self.assertRaises(RuntimeError):
                BudgetService(cost_model_path=path)

    def test_rate_limit_usage_uses_provided_now(self) -> None:
        snapshot = BudgetSnapshot(
            limit=5,
            window_seconds=30,
            cost_cap=0,
            error_budget_pct=0,
            cost_model_version='vX',
            budget_alert_pct=80,
        )
        fixed_now = datetime(2025, 1, 1, 12, 0, tzinfo=dt_timezone.utc)

        usage = BudgetService().rate_limit_usage(snapshot, now=fixed_now)

        expected_reset = (fixed_now + timedelta(seconds=snapshot.window_seconds)).isoformat()
        self.assertEqual(usage['limit'], snapshot.limit)
        self.assertEqual(usage['remaining'], snapshot.limit)
        self.assertEqual(usage['reset_at'], expected_reset)
