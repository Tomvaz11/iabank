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
        with use_tenant(seed_run.tenant_id):
            seed_run.refresh_from_db(fields=['started_at', 'status'])
        last_checkpoint_at = None
        for checkpoint in checkpoints:
            candidate = checkpoint.updated_at or checkpoint.created_at or current
            if last_checkpoint_at is None or candidate > last_checkpoint_at:
                last_checkpoint_at = candidate

        rpo_limit = current - timedelta(minutes=self.rpo_minutes)
        rto_limit = current - timedelta(minutes=self.rto_minutes)
        rpo_ok = last_checkpoint_at is not None and last_checkpoint_at >= rpo_limit
        rto_ok = seed_run.started_at is not None and seed_run.started_at >= rto_limit

        if rpo_ok and rto_ok:
            return None

        detail_parts = []
        if not rpo_ok:
            detail_parts.append(f'RPO<={self.rpo_minutes}min')
        if not rto_ok:
            detail_parts.append(f'RTO<={self.rto_minutes}min')
        detail = ' e '.join(detail_parts) or 'rpo_rto_violation'
        problem = ProblemDetail(
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            title='rpo_rto_violation',
            detail=detail,
            type='https://iabank.local/problems/seed/rpo-rto',
        )

        with use_tenant(seed_run.tenant_id):
            SeedRun.objects.filter(id=seed_run.id).update(
                status=SeedRun.Status.BLOCKED,
                reason=problem.as_dict(),
                updated_at=timezone.now(),
            )
        seed_run.status = SeedRun.Status.BLOCKED
        seed_run.reason = problem.as_dict()
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
        p95 = float(metrics.get('p95_ms', 0))
        p99 = float(metrics.get('p99_ms', 0))
        throughput_rps = float(metrics.get('throughput_rps', 0))
        error_rate = float(metrics.get('error_rate', 0))

        with use_tenant(seed_run.tenant_id):
            seed_run.refresh_from_db(fields=['status', 'error_budget_consumed', 'seed_profile'])
            profile = seed_run.seed_profile
            budget_cfg = profile.budget or {}
            error_budget_limit = float(budget_cfg.get('error_budget_pct', 0) or 0)
            p95_target = float(profile.slo_p95_ms or 0)
            p99_target = float(profile.slo_p99_ms or 0)
            throughput_target = float(profile.slo_throughput_rps or 0)

        consumed_pct = max(0.0, min(100.0, error_rate * 100))
        within_latency = (p95_target == 0 or p95 <= p95_target) and (p99_target == 0 or p99 <= p99_target)
        within_throughput = True  # throughput é monitorado, mas não bloqueante no gate
        within_budget = error_budget_limit == 0 or consumed_pct <= error_budget_limit

        if within_latency and within_throughput and within_budget:
            with use_tenant(seed_run.tenant_id):
                SeedRun.objects.filter(id=seed_run.id).update(
                    error_budget_consumed=Decimal(str(consumed_pct)),
                    updated_at=timezone.now(),
                )
            seed_run.error_budget_consumed = Decimal(str(consumed_pct))
            return None

        retry_after = max(1, int(profile.backoff.get('base_seconds', 60))) if profile and profile.backoff else 60
        detail_parts = [
            f'p95_ms={p95}>target={p95_target}',
            f'p99_ms={p99}>target={p99_target}',
            f'error_budget_pct={consumed_pct}>limit={error_budget_limit}',
        ]
        if not within_throughput:
            detail_parts.append(f'throughput_rps={throughput_rps}<target={throughput_target}')
        problem = ProblemDetail(
            status=HTTPStatus.TOO_MANY_REQUESTS,
            title='slo_budget_exceeded',
            detail='; '.join(detail_parts),
            type='https://iabank.local/problems/seed/slo-budget',
            retry_after=retry_after,
        )

        with use_tenant(seed_run.tenant_id):
            SeedRun.objects.filter(id=seed_run.id).update(
                status=SeedRun.Status.ABORTED,
                error_budget_consumed=Decimal(str(consumed_pct)),
                reason=problem.as_dict(),
                finished_at=current,
                updated_at=timezone.now(),
            )
        seed_run.status = SeedRun.Status.ABORTED
        seed_run.error_budget_consumed = Decimal(str(consumed_pct))
        seed_run.reason = problem.as_dict()
        seed_run.finished_at = current
        return problem
