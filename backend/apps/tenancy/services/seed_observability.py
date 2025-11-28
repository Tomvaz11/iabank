from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from http import HTTPStatus
from typing import Iterable, Mapping, Optional

from django.utils import timezone

from backend.apps.tenancy.managers import use_tenant
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
        current = now
        self._refresh_seed_run(seed_run, fields=['started_at', 'status'])
        last_checkpoint_at = self._last_checkpoint_time(checkpoints, fallback=current)
        rpo_ok = self._within_rpo(last_checkpoint_at, current)
        rto_ok = self._within_rto(seed_run.started_at, current)
        if rpo_ok and rto_ok:
            return None

        problem = self._rpo_problem(rpo_ok, rto_ok)
        self._mark_blocked(seed_run, problem, current)
        return problem

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
        current = now
        p95, p99, throughput_rps, error_rate = self._extract_metrics(metrics)
        profile = self._load_profile(seed_run)
        targets = self._targets_from_profile(profile)

        consumed_pct = max(0.0, min(100.0, error_rate * 100))
        if self._within_slo(p95, p99, consumed_pct, targets):
            self._persist_budget(seed_run, consumed_pct)
            return None

        problem = self._slo_problem(p95, p99, throughput_rps, consumed_pct, targets, profile)
        self._mark_aborted(seed_run, consumed_pct, current, problem)
        return problem

    def _refresh_seed_run(self, seed_run: SeedRun, *, fields: Iterable[str]) -> None:
        with use_tenant(seed_run.tenant_id):
            seed_run.refresh_from_db(fields=list(fields))

    @staticmethod
    def _last_checkpoint_time(checkpoints: Iterable[SeedCheckpoint], *, fallback: datetime) -> Optional[datetime]:
        latest = None
        for checkpoint in checkpoints:
            candidate = checkpoint.updated_at or checkpoint.created_at or fallback
            if latest is None or candidate > latest:
                latest = candidate
        return latest

    def _within_rpo(self, last_checkpoint_at: Optional[datetime], now: datetime) -> bool:
        if last_checkpoint_at is None:
            return False
        return last_checkpoint_at >= now - timedelta(minutes=self.rpo_minutes)

    def _within_rto(self, started_at: Optional[datetime], now: datetime) -> bool:
        if started_at is None:
            return False
        return started_at >= now - timedelta(minutes=self.rto_minutes)

    def _rpo_problem(self, rpo_ok: bool, rto_ok: bool) -> ProblemDetail:
        detail_parts = []
        if not rpo_ok:
            detail_parts.append(f'RPO<={self.rpo_minutes}min')
        if not rto_ok:
            detail_parts.append(f'RTO<={self.rto_minutes}min')
        detail = ' e '.join(detail_parts) or 'rpo_rto_violation'
        return ProblemDetail(
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            title='rpo_rto_violation',
            detail=detail,
            type='https://iabank.local/problems/seed/rpo-rto',
        )

    def _mark_blocked(self, seed_run: SeedRun, problem: ProblemDetail, now: datetime) -> None:
        with use_tenant(seed_run.tenant_id):
            SeedRun.objects.filter(id=seed_run.id).update(
                status=SeedRun.Status.BLOCKED,
                reason=problem.as_dict(),
                updated_at=timezone.now(),
            )
        seed_run.status = SeedRun.Status.BLOCKED
        seed_run.reason = problem.as_dict()

    @staticmethod
    def _extract_metrics(metrics: Mapping[str, float]) -> tuple[float, float, float, float]:
        return (
            float(metrics.get('p95_ms', 0)),
            float(metrics.get('p99_ms', 0)),
            float(metrics.get('throughput_rps', 0)),
            float(metrics.get('error_rate', 0)),
        )

    def _load_profile(self, seed_run: SeedRun):
        with use_tenant(seed_run.tenant_id):
            seed_run.refresh_from_db(fields=['status', 'error_budget_consumed', 'seed_profile'])
            return seed_run.seed_profile

    @staticmethod
    def _targets_from_profile(profile: SeedRun.seed_profile) -> dict[str, float]:
        budget_cfg = profile.budget or {}
        return {
            'error_budget_limit': float(budget_cfg.get('error_budget_pct', 0) or 0),
            'p95_target': float(profile.slo_p95_ms or 0),
            'p99_target': float(profile.slo_p99_ms or 0),
            'throughput_target': float(profile.slo_throughput_rps or 0),
            'backoff_base': int(profile.backoff.get('base_seconds', 60)) if profile and profile.backoff else 60,
        }

    @staticmethod
    def _within_slo(p95: float, p99: float, consumed_pct: float, targets: dict[str, float]) -> bool:
        within_latency = (targets['p95_target'] == 0 or p95 <= targets['p95_target']) and (
            targets['p99_target'] == 0 or p99 <= targets['p99_target']
        )
        within_budget = targets['error_budget_limit'] == 0 or consumed_pct <= targets['error_budget_limit']
        return within_latency and within_budget

    def _slo_problem(
        self,
        p95: float,
        p99: float,
        throughput_rps: float,
        consumed_pct: float,
        targets: dict[str, float],
        profile: SeedRun.seed_profile,
    ) -> ProblemDetail:
        retry_after = max(1, targets['backoff_base'])
        detail_parts = [
            f'p95_ms={p95}>target={targets["p95_target"]}',
            f'p99_ms={p99}>target={targets["p99_target"]}',
            f'error_budget_pct={consumed_pct}>limit={targets["error_budget_limit"]}',
        ]
        if targets['throughput_target'] and throughput_rps < targets['throughput_target']:
            detail_parts.append(f'throughput_rps={throughput_rps}<target={targets["throughput_target"]}')
        return ProblemDetail(
            status=HTTPStatus.TOO_MANY_REQUESTS,
            title='slo_budget_exceeded',
            detail='; '.join(detail_parts),
            type='https://iabank.local/problems/seed/slo-budget',
            retry_after=retry_after,
        )

    def _persist_budget(self, seed_run: SeedRun, consumed_pct: float) -> None:
        value = Decimal(str(consumed_pct))
        with use_tenant(seed_run.tenant_id):
            SeedRun.objects.filter(id=seed_run.id).update(
                error_budget_consumed=value,
                updated_at=timezone.now(),
            )
        seed_run.error_budget_consumed = value

    def _mark_aborted(self, seed_run: SeedRun, consumed_pct: float, now: datetime, problem: ProblemDetail) -> None:
        value = Decimal(str(consumed_pct))
        with use_tenant(seed_run.tenant_id):
            SeedRun.objects.filter(id=seed_run.id).update(
                status=SeedRun.Status.ABORTED,
                error_budget_consumed=value,
                reason=problem.as_dict(),
                finished_at=now,
                updated_at=timezone.now(),
            )
        seed_run.status = SeedRun.Status.ABORTED
        seed_run.error_budget_consumed = value
        seed_run.reason = problem.as_dict()
        seed_run.finished_at = now
