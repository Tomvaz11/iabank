from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from http import HTTPStatus
from typing import Optional
from uuid import UUID

from django.utils import timezone

from backend.apps.tenancy.services.seed_queue import QueueDecision, SeedQueueService


@dataclass
class ProblemDetail:
    status: int
    title: str
    detail: str
    type: str
    retry_after: Optional[int] = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            'status': self.status,
            'title': self.title,
            'detail': self.detail,
            'type': self.type,
        }
        if self.retry_after is not None:
            payload['retry_after'] = self.retry_after
        return payload


class SeedRunService:
    def __init__(self, queue_service: Optional[SeedQueueService] = None) -> None:
        self.queue_service = queue_service or SeedQueueService()

    def request_slot(
        self,
        *,
        environment: str,
        tenant_id: UUID,
        seed_run_id: Optional[UUID] = None,
        now: Optional[datetime] = None,
    ) -> tuple[QueueDecision, Optional[ProblemDetail]]:
        current_time = now or timezone.now()
        decision = self.queue_service.enqueue(
            environment=environment,
            tenant_id=tenant_id,
            seed_run_id=seed_run_id,
            now=current_time,
        )

        if decision.allowed:
            return decision, None

        return decision, self._build_problem(decision=decision, environment=environment)

    @staticmethod
    def exit_code_for(decision: QueueDecision) -> int:
        if decision.status_code == HTTPStatus.CONFLICT:
            return 3
        if decision.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            return 5
        return 1

    @staticmethod
    def _build_problem(decision: QueueDecision, environment: str) -> ProblemDetail:
        if decision.status_code == HTTPStatus.CONFLICT:
            return ProblemDetail(
                status=HTTPStatus.CONFLICT,
                title='global_concurrency_cap',
                detail=f'Limite global de execuções ativas atingido no ambiente {environment}.',
                type='https://iabank.local/problems/seed/global-cap',
                retry_after=decision.retry_after,
            )

        return ProblemDetail(
            status=HTTPStatus.TOO_MANY_REQUESTS,
            title='seed_queue_busy',
            detail=f'A fila de seeds do ambiente {environment} ainda possui itens pendentes dentro do TTL.',
            type='https://iabank.local/problems/seed/queue-ttl',
            retry_after=decision.retry_after,
        )
