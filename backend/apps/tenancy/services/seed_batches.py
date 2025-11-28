from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

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


class SeedBatchOrchestrator:
    """
    Orquestra reprocessamento de batches Celery (backoff/jitter/DLQ).
    Implementação real será adicionada nos itens de US3 (T051+).
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
        return BatchRetryPlan(
            retry_in_seconds=None,
            to_dlq=False,
            queue='seed_data.default',
            resume_token=checkpoint.resume_token if checkpoint else None,
            reason='not_implemented',
        )
