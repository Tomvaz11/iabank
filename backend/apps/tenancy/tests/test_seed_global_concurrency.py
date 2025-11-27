from __future__ import annotations

from datetime import datetime, timedelta
from http import HTTPStatus

from django.test import TestCase
from django.utils import timezone

from backend.apps.tenancy.models import SeedQueue, Tenant
from backend.apps.tenancy.services.seed_queue import QueueDecision, SeedQueueService


class SeedQueueServiceTest(TestCase):
    databases = {'default'}

    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            slug='tenant-queue',
            display_name='Tenant Queue',
            primary_domain='tenant-queue.iabank.local',
            pii_policy_version='v1',
        )
        self.service = SeedQueueService(max_active=2, ttl=timedelta(minutes=5))
        self.now = timezone.make_aware(datetime(2025, 1, 1, 12, 0, 0))

    def test_enqueue_creates_pending_entry_with_ttl(self) -> None:
        decision = self.service.enqueue(
            environment='staging',
            tenant_id=self.tenant.id,
            now=self.now,
        )

        self.assertIsInstance(decision, QueueDecision)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.status_code, HTTPStatus.ACCEPTED)
        self.assertIsNotNone(decision.entry)
        assert decision.entry  # help type checkers
        self.assertEqual(decision.entry.status, SeedQueue.Status.PENDING)
        self.assertEqual(decision.entry.expires_at, self.now + timedelta(minutes=5))

    def test_pending_entry_returns_retry_after(self) -> None:
        pending_expires_at = self.now + timedelta(minutes=5)
        SeedQueue.objects.unscoped().create(
            tenant=self.tenant,
            environment='staging',
            status=SeedQueue.Status.PENDING,
            enqueued_at=self.now,
            expires_at=pending_expires_at,
        )

        later = self.now + timedelta(minutes=1)
        decision = self.service.enqueue(
            environment='staging',
            tenant_id=self.tenant.id,
            now=later,
        )

        expected_retry = int((pending_expires_at - later).total_seconds())
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.status_code, HTTPStatus.TOO_MANY_REQUESTS)
        self.assertEqual(decision.retry_after, expected_retry)
        self.assertEqual(SeedQueue.objects.unscoped().count(), 1)

    def test_global_cap_conflict_when_queue_full(self) -> None:
        first_expiration = self.now + timedelta(minutes=2)
        second_expiration = self.now + timedelta(minutes=3)

        SeedQueue.objects.unscoped().create(
            tenant=self.tenant,
            environment='staging',
            status=SeedQueue.Status.STARTED,
            enqueued_at=self.now,
            expires_at=first_expiration,
        )
        SeedQueue.objects.unscoped().create(
            tenant=self.tenant,
            environment='staging',
            status=SeedQueue.Status.STARTED,
            enqueued_at=self.now,
            expires_at=second_expiration,
        )

        later = self.now + timedelta(minutes=1)
        decision = self.service.enqueue(
            environment='staging',
            tenant_id=self.tenant.id,
            now=later,
        )

        expected_retry = int((first_expiration - later).total_seconds())
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.status_code, HTTPStatus.CONFLICT)
        self.assertEqual(decision.retry_after, expected_retry)
        self.assertEqual(SeedQueue.objects.unscoped().count(), 2)

    def test_expired_entries_are_cleaned_before_admission(self) -> None:
        expired_time = self.now - timedelta(minutes=10)
        SeedQueue.objects.unscoped().create(
            tenant=self.tenant,
            environment='staging',
            status=SeedQueue.Status.PENDING,
            enqueued_at=expired_time,
            expires_at=expired_time + timedelta(minutes=1),
        )

        decision = self.service.enqueue(
            environment='staging',
            tenant_id=self.tenant.id,
            now=self.now,
        )

        expired_entries = SeedQueue.objects.unscoped().filter(status=SeedQueue.Status.EXPIRED).count()
        self.assertEqual(expired_entries, 1)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.status_code, HTTPStatus.ACCEPTED)

    def test_renew_marks_started_and_extends_ttl(self) -> None:
        decision = self.service.enqueue(
            environment='staging',
            tenant_id=self.tenant.id,
            now=self.now,
        )
        entry = decision.entry
        assert entry

        later = self.now + timedelta(minutes=2)
        renewed = self.service.renew(entry, now=later)

        refreshed = SeedQueue.objects.unscoped().get(id=entry.id)
        self.assertEqual(renewed.status, SeedQueue.Status.STARTED)
        self.assertEqual(refreshed.status, SeedQueue.Status.STARTED)
        self.assertEqual(renewed.expires_at, later + timedelta(minutes=5))
        self.assertEqual(refreshed.expires_at, later + timedelta(minutes=5))
