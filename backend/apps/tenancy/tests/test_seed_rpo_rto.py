from __future__ import annotations

from datetime import timedelta
from http import HTTPStatus

from django.test import TestCase
from django.utils import timezone

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedCheckpoint, SeedRun, Tenant
from backend.apps.tenancy.services.seed_observability import SeedObservabilityService
from backend.apps.tenancy.services.seed_runs import ProblemDetail, SeedRunService
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest


class SeedRpoRtoGateTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            slug='tenant-rpo',
            display_name='Tenant RPO',
            primary_domain='tenant-rpo.iabank.local',
            pii_policy_version='v1',
        )
        self.now = timezone.now()
        manifest = build_manifest(
            tenant_slug=self.tenant.slug,
            environment='staging',
            mode='dr',
        )
        creation = SeedRunService().create_seed_run(
            tenant_id=self.tenant.id,
            environment='staging',
            manifest=manifest,
            manifest_path='configs/seed_profiles/staging/tenant-rpo.yaml',
            idempotency_key='rpo-1',
            requested_by='svc-rpo',
            dry_run=False,
            mode='dr',
        )
        self.seed_run = creation.seed_run
        with use_tenant(self.tenant.id):
            SeedRun.objects.filter(id=self.seed_run.id).update(
                status=SeedRun.Status.RUNNING,
                started_at=self.now - timedelta(minutes=10),
            )
        self.gate = SeedObservabilityService(rpo_minutes=5, rto_minutes=60)

    def _create_checkpoint(self, minutes_ago: int) -> SeedCheckpoint:
        with use_tenant(self.tenant.id):
            checkpoint = SeedCheckpoint.objects.create(
                seed_run=self.seed_run,
                tenant=self.seed_run.tenant,
                entity='customers',
                hash_estado='hash-rpo',
                resume_token=b'cp-rpo',
                percentual_concluido=50,
            )
            SeedCheckpoint.objects.filter(id=checkpoint.id).update(
                created_at=self.now - timedelta(minutes=minutes_ago),
                updated_at=self.now - timedelta(minutes=minutes_ago),
            )
            return SeedCheckpoint.objects.get(id=checkpoint.id)

    def test_passes_when_checkpoint_and_duration_within_thresholds(self) -> None:
        checkpoint = self._create_checkpoint(minutes_ago=2)

        problem = self.gate.check_rpo_rto(
            seed_run=self.seed_run,
            checkpoints=[checkpoint],
            now=self.now,
        )

        self.assertIsNone(problem)
        self.seed_run.refresh_from_db()
        self.assertEqual(self.seed_run.status, SeedRun.Status.RUNNING)

    def test_blocks_runs_that_breach_rpo_or_rto(self) -> None:
        with use_tenant(self.tenant.id):
            SeedRun.objects.filter(id=self.seed_run.id).update(
                started_at=self.now - timedelta(minutes=75),
                status=SeedRun.Status.RUNNING,
            )
        stale_checkpoint = self._create_checkpoint(minutes_ago=12)

        problem = self.gate.check_rpo_rto(
            seed_run=self.seed_run,
            checkpoints=[stale_checkpoint],
            now=self.now,
        )

        self.assertIsInstance(problem, ProblemDetail)
        assert problem
        self.assertEqual(problem.status, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertEqual(problem.title, 'rpo_rto_violation')
        self.assertIn('RPO<=5min', problem.detail)
        self.assertIn('RTO<=60min', problem.detail)

        with use_tenant(self.tenant.id):
            refreshed = SeedRun.objects.get(id=self.seed_run.id)
            self.assertEqual(refreshed.status, SeedRun.Status.BLOCKED)
            self.assertIsNotNone(refreshed.reason)

    def test_blocks_when_no_checkpoint_or_start_time(self) -> None:
        with use_tenant(self.tenant.id):
            SeedRun.objects.filter(id=self.seed_run.id).update(started_at=None, status=SeedRun.Status.RUNNING)

        problem = self.gate.check_rpo_rto(
            seed_run=self.seed_run,
            checkpoints=[],
            now=self.now,
        )

        self.assertIsInstance(problem, ProblemDetail)
        assert problem
        self.assertEqual(problem.status, HTTPStatus.SERVICE_UNAVAILABLE)
        with use_tenant(self.tenant.id):
            refreshed = SeedRun.objects.get(id=self.seed_run.id)
            self.assertEqual(refreshed.status, SeedRun.Status.BLOCKED)
