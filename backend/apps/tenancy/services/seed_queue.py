from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Optional
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from backend.apps.tenancy.models import SeedQueue


@dataclass
class QueueDecision:
    allowed: bool
    status_code: int
    retry_after: Optional[int]
    entry: Optional[SeedQueue]
    reason: str


class SeedQueueService:
    def __init__(self, max_active: int = 2, ttl: timedelta = timedelta(minutes=5)) -> None:
        self.max_active = max_active
        self.ttl = ttl

    def enqueue(
        self,
        *,
        environment: str,
        tenant_id: Optional[UUID] = None,
        seed_run_id: Optional[UUID] = None,
        now: Optional[datetime] = None,
    ) -> QueueDecision:
        current_time = now or timezone.now()

        with transaction.atomic():
            self._expire_old_entries(environment=environment, now=current_time)

            active_entries = (
                SeedQueue.objects.unscoped()
                .select_for_update()
                .filter(
                    environment=environment,
                    status__in=[SeedQueue.Status.PENDING, SeedQueue.Status.STARTED],
                    expires_at__gt=current_time,
                )
                .order_by('expires_at')
            )

            pending = active_entries.filter(status=SeedQueue.Status.PENDING).first()
            if pending:
                retry_after = self._seconds_until(pending.expires_at, current_time)
                return QueueDecision(
                    allowed=False,
                    status_code=HTTPStatus.TOO_MANY_REQUESTS,
                    retry_after=retry_after,
                    entry=None,
                    reason='queue_pending_ttl',
                )

            if active_entries.count() >= self.max_active:
                next_expiration = active_entries.first().expires_at
                retry_after = self._seconds_until(next_expiration, current_time)
                return QueueDecision(
                    allowed=False,
                    status_code=HTTPStatus.CONFLICT,
                    retry_after=retry_after,
                    entry=None,
                    reason='global_concurrency_cap',
                )

            entry = SeedQueue.objects.unscoped().create(
                tenant_id=tenant_id,
                environment=environment,
                seed_run_id=seed_run_id,
                status=SeedQueue.Status.PENDING,
                enqueued_at=current_time,
                expires_at=current_time + self.ttl,
            )

        return QueueDecision(
            allowed=True,
            status_code=HTTPStatus.ACCEPTED,
            retry_after=None,
            entry=entry,
            reason='queued',
        )

    def renew(self, entry: SeedQueue, now: Optional[datetime] = None) -> SeedQueue:
        """
        Reagenda o slot na fila quando o worker assume o processamento.
        """
        current_time = now or timezone.now()
        entry.status = SeedQueue.Status.STARTED
        entry.expires_at = current_time + self.ttl
        entry.save(update_fields=['status', 'expires_at', 'updated_at'])
        return entry

    def _expire_old_entries(self, *, environment: str, now: datetime) -> None:
        expired = SeedQueue.objects.unscoped().filter(
            environment=environment,
            status__in=[SeedQueue.Status.PENDING, SeedQueue.Status.STARTED],
            expires_at__lte=now,
        )
        expired.update(status=SeedQueue.Status.EXPIRED, updated_at=now)

    @staticmethod
    def _seconds_until(target: datetime, now: datetime) -> int:
        delta = target - now
        seconds = int(delta.total_seconds())
        return max(seconds, 0)
