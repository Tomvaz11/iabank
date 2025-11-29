from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedDataset


class SeedDatasetGC:
    """
    Limpa datasets de seeds por modo/tenant para evitar inflação e respeitar TTL.
    """

    def cleanup_for_mode(self, *, tenant_id, environment: str, mode: str) -> int:
        """
        Remove datasets existentes para o modo/ambiente antes de uma nova execução.
        """
        with use_tenant(tenant_id):
            qs = SeedDataset.objects.filter(seed_run__environment=environment, seed_run__mode=mode)
            deleted, _ = qs.delete()
        return deleted

    def expire_by_ttl(
        self,
        *,
        tenant_id,
        days: int,
        environment: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> int:
        """
        Remove datasets mais antigos que o TTL configurado.
        """
        if days <= 0:
            return 0

        current = now or timezone.now()
        cutoff = current - timedelta(days=days)
        with use_tenant(tenant_id):
            qs = SeedDataset.objects.filter(created_at__lt=cutoff)
            if environment:
                qs = qs.filter(seed_run__environment=environment)
            deleted, _ = qs.delete()
        return deleted
