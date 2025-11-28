from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from http import HTTPStatus
from typing import Any, Mapping, Optional

import structlog
from django.utils import timezone

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedRun
from backend.apps.tenancy.services.seed_runs import ProblemDetail


@dataclass(frozen=True)
class FlagSnapshot:
    canary_enabled: bool
    rollback_rehearsed: bool


class SeedFeatureFlags:
    """
    Avaliação de flags específicas do seed_data.
    - canary só é permitido quando mode=canary
    - rollback ensaiado indicado para canary/DR
    """

    def __init__(self, *, allowed_canary_modes: Optional[set[str]] = None) -> None:
        self.allowed_canary_modes = allowed_canary_modes or {'canary'}

    def ensure_canary_scope(self, *, manifest: Mapping[str, Any], mode: str) -> Optional[ProblemDetail]:
        """
        Falha se o manifesto declarar bloco `canary` fora do modo canary.
        """
        has_canary_scope = bool(manifest.get('canary')) if isinstance(manifest, Mapping) else False
        if has_canary_scope and mode not in self.allowed_canary_modes:
            return ProblemDetail(
                status=HTTPStatus.FORBIDDEN,
                title='canary_flag_not_allowed',
                detail='Flag canary só é permitida quando mode=canary.',
                type='https://iabank.local/problems/seed/canary-flag',
            )
        return None

    def snapshot(self, *, mode: str) -> FlagSnapshot:
        return FlagSnapshot(
            canary_enabled=mode in self.allowed_canary_modes,
            rollback_rehearsed=mode in {'canary', 'dr'},
        )


class SeedDORAMetrics:
    """
    Calcula métricas DORA por tenant e registra snapshot estruturado.
    """

    def __init__(self, *, window_days: int = 14) -> None:
        self.window_days = window_days
        self.logger = structlog.get_logger('seed.dora')

    def snapshot(self, *, seed_run: SeedRun) -> dict[str, object]:
        now = timezone.now()
        window_start = now - timedelta(days=self.window_days)
        with use_tenant(seed_run.tenant_id):
            runs = (
                SeedRun.objects.unscoped()
                .filter(tenant_id=seed_run.tenant_id, created_at__gte=window_start)
                .all()
            )

        total = len(runs)
        succeeded = [run for run in runs if run.status == SeedRun.Status.SUCCEEDED]
        failed = [
            run
            for run in runs
            if run.status
            in {SeedRun.Status.FAILED, SeedRun.Status.ABORTED, SeedRun.Status.BLOCKED}
        ]

        deployment_frequency = round(total / self.window_days, 4) if self.window_days else 0.0
        change_failure_rate = round(len(failed) / max(1, len(failed) + len(succeeded)), 4)
        mttr_minutes = self._mean_minutes(failed)
        lead_time_minutes = self._mean_minutes(succeeded, field_start='created_at', field_end='finished_at')

        snapshot = {
            'window_days': self.window_days,
            'deployments': total,
            'deployment_frequency_per_day': deployment_frequency,
            'change_failure_rate': change_failure_rate,
            'mttr_minutes': mttr_minutes,
            'lead_time_minutes': lead_time_minutes,
            'rollback_rehearsed': seed_run.mode in {'canary', 'dr', 'carga'},
        }

        self.logger.info(
            'seed_dora_snapshot',
            seed_run_id=str(seed_run.id),
            tenant_id=str(seed_run.tenant_id),
            **snapshot,
        )
        return snapshot

    def _mean_minutes(
        self,
        runs: list[SeedRun],
        *,
        field_start: str = 'started_at',
        field_end: str = 'finished_at',
    ) -> float:
        durations: list[float] = []
        for run in runs:
            start = getattr(run, field_start, None)
            end = getattr(run, field_end, None)
            if start and end:
                durations.append((end - start).total_seconds() / 60.0)
        if not durations:
            return 0.0
        return round(sum(durations) / len(durations), 4)
