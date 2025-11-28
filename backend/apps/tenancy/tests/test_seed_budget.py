from __future__ import annotations

from http import HTTPStatus

from django.test import TestCase

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import BudgetRateLimit, Tenant
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
