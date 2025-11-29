from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedBatch, SeedCheckpoint


@dataclass
class BackoffConfig:
    base_seconds: int
    jitter_factor: float
    max_retries: int
    max_interval_seconds: int


@dataclass
class BatchRetryPlan:
    retry_in_seconds: Optional[int]
    to_dlq: bool
    queue: str
    resume_token: Optional[bytes] = None
    reason: Optional[str] = None


class SandboxOutboxRouter:
    """
    Roteia eventos/outbox para um sink seguro (sandbox), removendo URLs reais.
    """

    def __init__(self, sink: str = 'sandbox') -> None:
        self.sink = sink

    def route(self, *, event: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = dict(event)
        sanitized['sink'] = self.sink
        sanitized.pop('target_url', None)
        return sanitized


class SeedBatchOrchestrator:
    """
    Orquestra reprocessamento de batches Celery (backoff/jitter/DLQ) para modos carga/DR.
    """

    def __init__(
        self,
        backoff: BackoffConfig,
        random_generator: Callable[[float, float], float] | None = None,
    ) -> None:
        self.backoff = backoff
        self.random_generator = random_generator

    def plan_retry(
        self,
        *,
        batch: SeedBatch,
        checkpoint: SeedCheckpoint | None,
        status_code: int,
        now: datetime,
    ) -> BatchRetryPlan:
        """
        Retorna um plano de retry/DLQ para o batch com base no status informado.
        A lógica será preenchida na implementação da US3.
        """
        current = now
        queue = self._queue_for(batch)
        with use_tenant(batch.tenant_id):
            batch.refresh_from_db()

            if batch.attempt >= self.backoff.max_retries:
                batch.status = SeedBatch.Status.DLQ
                batch.dlq_attempts = batch.dlq_attempts + 1
                batch.last_retry_at = current
                batch.next_retry_at = None
                batch.save(update_fields=['status', 'dlq_attempts', 'last_retry_at', 'next_retry_at', 'updated_at'])
                return BatchRetryPlan(
                    retry_in_seconds=None,
                    to_dlq=True,
                    queue='seed_data.dlq',
                    resume_token=checkpoint.resume_token if checkpoint else None,
                    reason='too_many_retries',
                )

            delay_seconds = self._compute_delay_seconds(batch.attempt)
            batch.attempt = batch.attempt + 1
            batch.status = SeedBatch.Status.PENDING
            batch.last_retry_at = current
            batch.next_retry_at = current + timedelta(seconds=delay_seconds)
            batch.save(update_fields=['attempt', 'status', 'last_retry_at', 'next_retry_at', 'updated_at'])

        reason = 'rate_limited' if status_code == 429 else 'transient_failure'
        return BatchRetryPlan(
            retry_in_seconds=delay_seconds,
            to_dlq=False,
            queue=queue,
            resume_token=checkpoint.resume_token if checkpoint else None,
            reason=reason,
        )

    def _compute_delay_seconds(self, attempt: int) -> int:
        """
        Calcula delay exponencial com jitter, limitado por max_interval_seconds.
        """
        base_delay = self.backoff.base_seconds * (2 ** (attempt + 1))
        capped_delay = min(self.backoff.max_interval_seconds, base_delay)
        low = capped_delay * (1 - self.backoff.jitter_factor)
        high = capped_delay * (1 + self.backoff.jitter_factor)
        jittered = self.random_generator(low, high) if self.random_generator else random.uniform(low, high)
        return max(1, int(jittered))

    @staticmethod
    def _queue_for(batch: SeedBatch) -> str:
        mode = getattr(getattr(batch, 'seed_run', None), 'mode', None)
        if mode in {'carga', 'dr'}:
            return 'seed_data.load_dr'
        return 'seed_data.default'
