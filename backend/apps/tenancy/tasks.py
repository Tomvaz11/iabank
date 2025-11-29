from __future__ import annotations

import structlog
from celery import shared_task
from django.utils import timezone

from backend.apps.tenancy.models import SeedBatch, SeedCheckpoint, SeedRun
from backend.apps.tenancy.services.seed_batches import BackoffConfig, SeedBatchOrchestrator
from backend.apps.tenancy.services.seed_observability import SeedObservabilityService
from backend.apps.tenancy.services.seed_runs import ProblemDetail

logger = structlog.get_logger(__name__)


@shared_task(
    name='seed_data.dispatch_baseline',
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    queue='seed_data.default',
)
def dispatch_baseline(self, seed_run_id: str, tenant_id: str) -> dict[str, str]:
    """
    Enfileira execuções baseline na fila default com acks tardios.
    """
    routing_key = self.request.delivery_info.get('routing_key') if hasattr(self, 'request') else None
    logger.info(
        'seed_queue_baseline',
        seed_run_id=seed_run_id,
        tenant_id=tenant_id,
        queue=routing_key or 'seed_data.default',
    )
    return {'seed_run_id': seed_run_id, 'queue': routing_key or 'seed_data.default'}


@shared_task(
    name='seed_data.dispatch_load_dr',
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    queue='seed_data.load_dr',
)
def dispatch_load_dr(self, seed_run_id: str, tenant_id: str) -> dict[str, str]:
    """
    Enfileira execuções de carga/DR em fila dedicada com acks tardios.
    """
    routing_key = self.request.delivery_info.get('routing_key') if hasattr(self, 'request') else None
    logger.info(
        'seed_queue_load_dr',
        seed_run_id=seed_run_id,
        tenant_id=tenant_id,
        queue=routing_key or 'seed_data.load_dr',
    )
    return {'seed_run_id': seed_run_id, 'queue': routing_key or 'seed_data.load_dr'}


@shared_task(
    name='seed_data.handle_dlq',
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    queue='seed_data.dlq',
)
def handle_dlq(self, seed_run_id: str, tenant_id: str, reason: str | None = None) -> dict[str, str | None]:
    """
    Stub de DLQ para execuções que excederem tentativas ou forem reprocessadas.
    """
    routing_key = self.request.delivery_info.get('routing_key') if hasattr(self, 'request') else None
    logger.warning(
        'seed_queue_dlq',
        seed_run_id=seed_run_id,
        tenant_id=tenant_id,
        reason=reason or 'dlq',
        queue=routing_key or 'seed_data.dlq',
    )
    return {
        'seed_run_id': seed_run_id,
        'queue': routing_key or 'seed_data.dlq',
        'reason': reason or 'dlq',
    }


def _backoff_from_profile(seed_run: SeedRun) -> BackoffConfig:
    profile_backoff = seed_run.seed_profile.backoff if seed_run.seed_profile else {}
    return BackoffConfig(
        base_seconds=int(profile_backoff.get('base_seconds', 1) or 1),
        jitter_factor=float(profile_backoff.get('jitter_factor', 0.1) or 0.0),
        max_retries=int(profile_backoff.get('max_retries', 3) or 0),
        max_interval_seconds=int(profile_backoff.get('max_interval_seconds', 60) or 60),
    )


@shared_task(
    name='seed_data.retry_batch',
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    queue='seed_data.load_dr',
)
def retry_seed_batch(
    self,
    batch_id: str,
    status_code: int,
    checkpoint_id: str | None = None,
    auto_dispatch: bool = True,
) -> dict[str, object]:
    """
    Reagenda um batch com backoff/jitter ou envia para DLQ quando exceder tentativas.
    """
    now = timezone.now()
    batch = (
        SeedBatch.objects.unscoped()
        .select_related('seed_run', 'seed_run__seed_profile')
        .filter(id=batch_id)
        .first()
    )
    if not batch or batch.seed_run is None:
        return {'status': 'not_found', 'batch_id': batch_id}

    checkpoint = (
        SeedCheckpoint.objects.unscoped().filter(id=checkpoint_id).first() if checkpoint_id else None
    )

    orchestrator = SeedBatchOrchestrator(_backoff_from_profile(batch.seed_run))
    plan = orchestrator.plan_retry(
        batch=batch,
        checkpoint=checkpoint,
        status_code=int(status_code),
        now=now,
    )

    if auto_dispatch:
        if plan.to_dlq:
            handle_dlq.apply_async(
                args=[str(batch.seed_run_id), str(batch.tenant_id), plan.reason],
                queue=plan.queue,
            )
        else:
            dispatch = dispatch_load_dr if plan.queue == 'seed_data.load_dr' else dispatch_baseline
            dispatch.apply_async(
                args=[str(batch.seed_run_id), str(batch.tenant_id)],
                countdown=plan.retry_in_seconds or 0,
                queue=plan.queue,
            )

    return {
        'batch_id': str(batch.id),
        'queue': plan.queue,
        'retry_in_seconds': plan.retry_in_seconds,
        'to_dlq': plan.to_dlq,
        'reason': plan.reason,
        'resume_token': plan.resume_token.decode() if isinstance(plan.resume_token, (bytes, bytearray)) else plan.resume_token,
    }


@shared_task(
    name='seed_data.check_runtime_slo',
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    queue='seed_data.default',
)
def check_runtime_slo(self, seed_run_id: str, metrics: dict[str, float]) -> dict[str, object]:
    """
    Gate de SLO/error budget em runtime para abortar runs que excederem limites.
    """
    seed_run = SeedRun.objects.unscoped().select_related('seed_profile').filter(id=seed_run_id).first()
    if not seed_run:
        return {'status': 'not_found', 'seed_run_id': seed_run_id}

    gate = SeedObservabilityService()
    problem = gate.check_runtime_slo(seed_run=seed_run, metrics=metrics, now=timezone.now())
    return {
        'seed_run_id': str(seed_run.id),
        'status': 'aborted' if problem else 'ok',
        'problem': problem.as_dict() if isinstance(problem, ProblemDetail) else None,
    }
