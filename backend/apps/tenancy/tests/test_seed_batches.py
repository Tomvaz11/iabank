from __future__ import annotations

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from backend.apps.tenancy import tasks as seed_tasks
from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedBatch, SeedCheckpoint, Tenant
from backend.apps.tenancy.services.seed_batches import (
    BackoffConfig,
    BatchRetryPlan,
    SandboxOutboxRouter,
    SeedBatchOrchestrator,
)
from backend.apps.tenancy.services.seed_runs import SeedRunService
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest


class SeedBatchOrchestratorTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            slug='tenant-batches',
            display_name='Tenant Batches',
            primary_domain='tenant-batches.iabank.local',
            pii_policy_version='v1',
        )
        self.run_service = SeedRunService()
        manifest = build_manifest(
            tenant_slug=self.tenant.slug,
            environment='staging',
            mode='carga',
        )
        creation = self.run_service.create_seed_run(
            tenant_id=self.tenant.id,
            environment='staging',
            manifest=manifest,
            manifest_path='configs/seed_profiles/staging/tenant-batches.yaml',
            idempotency_key='seed-batches-1',
            requested_by='svc-seeds',
            dry_run=False,
            mode='carga',
        )
        self.seed_run = creation.seed_run
        with use_tenant(self.tenant.id):
            self.batch = SeedBatch.objects.filter(seed_run=self.seed_run, entity='customers').first()
        assert self.batch

        self.backoff = BackoffConfig(
            base_seconds=2,
            jitter_factor=0.2,
            max_retries=2,
            max_interval_seconds=30,
        )
        self.orchestrator = SeedBatchOrchestrator(
            self.backoff,
            random_generator=lambda low, high: (low + high) / 2,  # determinístico nos testes
        )
        self.now = timezone.now()

    def test_transient_failure_schedules_retry_with_checkpoint_resume(self) -> None:
        with use_tenant(self.tenant.id):
            checkpoint = SeedCheckpoint.objects.create(
                seed_run=self.seed_run,
                tenant=self.seed_run.tenant,
                entity=self.batch.entity,
                hash_estado='hash-1',
                resume_token=b'checkpoint-1',
                percentual_concluido=25,
            )

        plan = self.orchestrator.plan_retry(
            batch=self.batch,
            checkpoint=checkpoint,
            status_code=429,
            now=self.now,
        )

        self.assertIsInstance(plan, BatchRetryPlan)
        self.assertFalse(plan.to_dlq)
        self.assertIsNotNone(plan.retry_in_seconds)

        expected_delay = min(
            self.backoff.max_interval_seconds,
            self.backoff.base_seconds * (2**1),
        )
        lower_bound = int(expected_delay * (1 - self.backoff.jitter_factor))
        upper_bound = int(expected_delay * (1 + self.backoff.jitter_factor))
        assert plan.retry_in_seconds is not None
        self.assertGreaterEqual(plan.retry_in_seconds, lower_bound)
        self.assertLessEqual(plan.retry_in_seconds, upper_bound)
        self.assertEqual(plan.queue, 'seed_data.load_dr')
        self.assertEqual(plan.resume_token, checkpoint.resume_token)

        with use_tenant(self.tenant.id):
            refreshed = SeedBatch.objects.get(id=self.batch.id)
            self.assertEqual(refreshed.status, SeedBatch.Status.PENDING)
            self.assertEqual(refreshed.attempt, 1)
            self.assertIsNotNone(refreshed.next_retry_at)
            if refreshed.next_retry_at:
                delta = refreshed.next_retry_at - self.now
                self.assertGreater(delta, timedelta(seconds=0))
                self.assertLess(delta, timedelta(minutes=5))

    def test_max_retries_route_batch_to_dlq(self) -> None:
        with use_tenant(self.tenant.id):
            SeedBatch.objects.filter(id=self.batch.id).update(attempt=self.backoff.max_retries)

        plan = self.orchestrator.plan_retry(
            batch=self.batch,
            checkpoint=None,
            status_code=429,
            now=self.now,
        )

        self.assertTrue(plan.to_dlq)
        self.assertIsNone(plan.retry_in_seconds)
        self.assertEqual(plan.queue, 'seed_data.dlq')
        self.assertEqual(plan.reason, 'too_many_retries')

        with use_tenant(self.tenant.id):
            refreshed = SeedBatch.objects.get(id=self.batch.id)
            self.assertEqual(refreshed.status, SeedBatch.Status.DLQ)
            self.assertEqual(refreshed.dlq_attempts, 1)
            self.assertIsNone(refreshed.next_retry_at)

    def test_backoff_caps_next_retry_at_max_interval(self) -> None:
        capped_policy = BackoffConfig(
            base_seconds=5,
            jitter_factor=0.1,
            max_retries=5,
            max_interval_seconds=10,
        )
        orchestrator = SeedBatchOrchestrator(capped_policy, random_generator=lambda low, high: high)
        with use_tenant(self.tenant.id):
            SeedBatch.objects.filter(id=self.batch.id).update(attempt=3)

        plan = orchestrator.plan_retry(
            batch=self.batch,
            checkpoint=None,
            status_code=429,
            now=self.now,
        )

        self.assertIsInstance(plan, BatchRetryPlan)
        self.assertIsNotNone(plan.retry_in_seconds)
        assert plan.retry_in_seconds is not None
        self.assertLessEqual(plan.retry_in_seconds, int(capped_policy.max_interval_seconds * 1.1))
        self.assertEqual(plan.queue, 'seed_data.load_dr')


class SandboxOutboxRouterTest(TestCase):
    databases = {'default'}

    def test_routes_outbox_event_to_sandbox_sink(self) -> None:
        router = SandboxOutboxRouter()
        routed = router.route(
            event={
                'entity': 'customers',
                'payload': {'id': 1},
                'target_url': 'https://api.real.example',
            }
        )

        self.assertEqual(routed['sink'], 'sandbox')
        self.assertEqual(routed['entity'], 'customers')
        self.assertNotIn('target_url', routed)


class SeedBatchCeleryTaskTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            slug='tenant-batches-celery',
            display_name='Tenant Batches Celery',
            primary_domain='tenant-batches-celery.iabank.local',
            pii_policy_version='v1',
        )
        manifest = build_manifest(tenant_slug=self.tenant.slug, environment='staging', mode='carga')
        creation = SeedRunService().create_seed_run(
            tenant_id=self.tenant.id,
            environment='staging',
            manifest=manifest,
            manifest_path='configs/seed_profiles/staging/tenant-batches-celery.yaml',
            idempotency_key='seed-batches-celery-1',
            requested_by='svc-seeds',
            dry_run=False,
            mode='carga',
        )
        with use_tenant(self.tenant.id):
            self.batch = SeedBatch.objects.filter(seed_run=creation.seed_run, entity='customers').first()
        assert self.batch

    def test_retry_seed_batch_routes_to_dlq_when_max_retries(self) -> None:
        with use_tenant(self.tenant.id):
            SeedBatch.objects.filter(id=self.batch.id).update(attempt=3)

        result = seed_tasks.retry_seed_batch.__wrapped__.__func__(  # type: ignore[attr-defined]
            None,
            str(self.batch.id),
            429,
            auto_dispatch=False,
        )

        self.assertTrue(result['to_dlq'])
        self.assertEqual(result['queue'], 'seed_data.dlq')
        self.assertEqual(result['reason'], 'too_many_retries')

    def test_retry_seed_batch_schedules_retry_with_reason(self) -> None:
        with use_tenant(self.tenant.id):
            SeedBatch.objects.filter(id=self.batch.id).update(attempt=0)
            checkpoint = SeedCheckpoint.objects.create(
                seed_run=self.batch.seed_run,
                tenant=self.batch.tenant,
                entity=self.batch.entity,
                hash_estado='hash-2',
                resume_token=b'token-2',
                percentual_concluido=10,
            )

        result = seed_tasks.retry_seed_batch.__wrapped__.__func__(  # type: ignore[attr-defined]
            None,
            str(self.batch.id),
            429,
            checkpoint_id=str(checkpoint.id),
            auto_dispatch=False,
        )

        self.assertFalse(result['to_dlq'])
        self.assertEqual(result['queue'], 'seed_data.load_dr')
        self.assertEqual(result['reason'], 'rate_limited')
        self.assertIsNotNone(result['retry_in_seconds'])
