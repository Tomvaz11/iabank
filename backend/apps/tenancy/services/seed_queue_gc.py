from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone

from backend.apps.tenancy.models import SeedQueue, SeedRun


class SeedQueueGC:
    def __init__(self, ttl: Optional[timedelta] = None) -> None:
        self.ttl = ttl or timedelta(minutes=5)

    def expire_stale(self, *, environment: str, now: Optional[datetime] = None) -> int:
        current = now or timezone.now()
        stale = SeedQueue.objects.unscoped().filter(
            environment=environment,
            status__in=[SeedQueue.Status.PENDING, SeedQueue.Status.STARTED],
            expires_at__lte=current,
        )
        deleted = stale.update(status=SeedQueue.Status.EXPIRED, updated_at=current)
        return deleted

    def release_for_run(self, seed_run: SeedRun, *, now: Optional[datetime] = None) -> int:
        current = now or timezone.now()
        qs = SeedQueue.objects.unscoped().filter(
            seed_run_id=seed_run.id,
            status__in=[SeedQueue.Status.PENDING, SeedQueue.Status.STARTED],
        )
        return qs.update(status=SeedQueue.Status.EXPIRED, expires_at=current, updated_at=current)

    def renew_if_needed(self, entry: SeedQueue, *, now: Optional[datetime] = None) -> SeedQueue:
        current = now or timezone.now()
        if entry.expires_at > current:
            return entry
        entry.expires_at = current + self.ttl
        entry.save(update_fields=['expires_at', 'updated_at'])
        return entry
