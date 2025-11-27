from __future__ import annotations

import structlog
from celery import shared_task

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
