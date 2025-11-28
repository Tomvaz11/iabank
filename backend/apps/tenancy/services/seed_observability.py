from __future__ import annotations

from datetime import datetime
from typing import Iterable, Mapping, Optional

from backend.apps.tenancy.models import SeedCheckpoint, SeedRun
from backend.apps.tenancy.services.seed_runs import ProblemDetail


class SeedObservabilityService:
    """
    Gates de RPO/RTO e SLO/error budget para execuções de seeds.
    Implementação será concluída nos itens da US3 (T049/T050/T062).
    """

    def __init__(self, rpo_minutes: int = 5, rto_minutes: int = 60) -> None:
        self.rpo_minutes = rpo_minutes
        self.rto_minutes = rto_minutes

    def check_rpo_rto(
        self,
        *,
        seed_run: SeedRun,
        checkpoints: Iterable[SeedCheckpoint],
        now: datetime,
    ) -> Optional[ProblemDetail]:
        """
        Avalia se RPO/RTO foram violados. Retorna ProblemDetail em caso de falha.
        """
        return None

    def check_runtime_slo(
        self,
        *,
        seed_run: SeedRun,
        metrics: Mapping[str, float],
        now: datetime,
    ) -> Optional[ProblemDetail]:
        """
        Avalia métricas runtime (p95/p99/throughput/error_rate) e budget.
        """
        return None
