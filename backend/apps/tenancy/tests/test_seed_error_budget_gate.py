from __future__ import annotations

from datetime import timedelta
from http import HTTPStatus

from django.test import TestCase
from django.utils import timezone

from backend.apps.tenancy import tasks as seed_tasks
from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedRun, Tenant
from backend.apps.tenancy.services.seed_observability import SeedObservabilityService
from backend.apps.tenancy.services.seed_runs import ProblemDetail, SeedRunService
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest


class SeedErrorBudgetGateTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            slug='tenant-budget',
            display_name='Tenant Budget',
            primary_domain='tenant-budget.iabank.local',
            pii_policy_version='v1',
        )
        self.now = timezone.now()
        self.gate = SeedObservabilityService()

    def _create_seed_run(self, overrides: dict | None = None) -> SeedRun:
        manifest = build_manifest(
            tenant_slug=self.tenant.slug,
            environment='staging',
            mode='dr',
            overrides=overrides or {},
        )
        creation = SeedRunService().create_seed_run(
            tenant_id=self.tenant.id,
            environment='staging',
            manifest=manifest,
            manifest_path='configs/seed_profiles/staging/tenant-budget.yaml',
            idempotency_key=manifest['integrity']['manifest_hash'],
            requested_by='svc-budget',
            dry_run=False,
            mode='dr',
        )
        with use_tenant(self.tenant.id):
            SeedRun.objects.filter(id=creation.seed_run.id).update(
                status=SeedRun.Status.RUNNING,
                started_at=self.now - timedelta(minutes=5),
            )
        return creation.seed_run

    def test_allows_run_when_metrics_within_slo_and_budget(self) -> None:
        run = self._create_seed_run(
            overrides={
                'slo': {'p95_target_ms': 900, 'p99_target_ms': 1400, 'throughput_target_rps': 15},
                'budget': {'error_budget_pct': 20},
            }
        )
        metrics = {'p95_ms': 500, 'p99_ms': 700, 'throughput_rps': 10, 'error_rate': 0.05}

        problem = self.gate.check_runtime_slo(
            seed_run=run,
            metrics=metrics,
            now=self.now,
        )

        self.assertIsNone(problem)
        run.refresh_from_db()
        self.assertEqual(run.status, SeedRun.Status.RUNNING)
        self.assertAlmostEqual(float(run.error_budget_consumed), 5.0, delta=0.01)

    def test_aborts_when_latency_or_error_budget_exceeds_targets(self) -> None:
        run = self._create_seed_run(
            overrides={
                'slo': {'p95_target_ms': 400, 'p99_target_ms': 800, 'throughput_target_rps': 5},
                'budget': {'error_budget_pct': 10},
            }
        )
        metrics = {'p95_ms': 1200, 'p99_ms': 1900, 'throughput_rps': 9, 'error_rate': 0.15}

        problem = self.gate.check_runtime_slo(
            seed_run=run,
            metrics=metrics,
            now=self.now,
        )

        self.assertIsInstance(problem, ProblemDetail)
        assert problem
        self.assertEqual(problem.status, HTTPStatus.TOO_MANY_REQUESTS)
        self.assertEqual(problem.title, 'slo_budget_exceeded')
        self.assertIsNotNone(problem.retry_after)
        self.assertIn('p95_ms', problem.detail)
        self.assertIn('error_budget_pct', problem.detail)

        with use_tenant(self.tenant.id):
            refreshed = SeedRun.objects.get(id=run.id)
            self.assertEqual(refreshed.status, SeedRun.Status.ABORTED)
            self.assertGreaterEqual(float(refreshed.error_budget_consumed), 15.0)
            self.assertIsNotNone(refreshed.reason)

    def test_celery_task_check_runtime_slo_aborts_run(self) -> None:
        run = self._create_seed_run(
            overrides={
                'slo': {'p95_target_ms': 300, 'p99_target_ms': 500, 'throughput_target_rps': 5},
                'budget': {'error_budget_pct': 5},
            }
        )
        metrics = {'p95_ms': 800, 'p99_ms': 900, 'throughput_rps': 1, 'error_rate': 0.1}

        result = seed_tasks.check_runtime_slo.__wrapped__.__func__(  # type: ignore[attr-defined]
            None,
            str(run.id),
            metrics,
        )

        self.assertEqual(result['status'], 'aborted')
        with use_tenant(self.tenant.id):
            refreshed = SeedRun.objects.get(id=run.id)
            self.assertEqual(refreshed.status, SeedRun.Status.ABORTED)
