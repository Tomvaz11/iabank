from __future__ import annotations

from datetime import datetime
from http import HTTPStatus
from uuid import uuid4

from django.test import SimpleTestCase

from backend.apps.tenancy.services.seed_queue import QueueDecision
from backend.apps.tenancy.services.seed_runs import ProblemDetail, SeedRunService


class _StubQueueService:
    def __init__(self, decision: QueueDecision) -> None:
        self.decision = decision
        self.called_with: dict[str, object] | None = None

    def enqueue(self, **kwargs) -> QueueDecision:
        self.called_with = kwargs
        return self.decision


class SeedRunServiceTest(SimpleTestCase):
    def test_request_slot_allows_when_queue_accepts(self) -> None:
        decision = QueueDecision(
            allowed=True,
            status_code=HTTPStatus.ACCEPTED,
            retry_after=None,
            entry=None,
            reason='queued',
        )
        service = SeedRunService(queue_service=_StubQueueService(decision))

        result_decision, problem = service.request_slot(
            environment='staging',
            tenant_id=uuid4(),
            seed_run_id=None,
            now=datetime(2025, 1, 1, 12, 0, 0),
        )

        self.assertTrue(result_decision.allowed)
        self.assertIsNone(problem)

    def test_request_slot_conflict_builds_problem_detail(self) -> None:
        decision = QueueDecision(
            allowed=False,
            status_code=HTTPStatus.CONFLICT,
            retry_after=42,
            entry=None,
            reason='global_concurrency_cap',
        )
        service = SeedRunService(queue_service=_StubQueueService(decision))

        _, problem = service.request_slot(
            environment='staging',
            tenant_id=uuid4(),
            seed_run_id=None,
            now=datetime(2025, 1, 1, 12, 0, 0),
        )

        self.assertIsInstance(problem, ProblemDetail)
        assert problem
        self.assertEqual(problem.status, HTTPStatus.CONFLICT)
        self.assertEqual(problem.title, 'global_concurrency_cap')
        self.assertEqual(problem.retry_after, 42)
        self.assertEqual(SeedRunService.exit_code_for(decision), 3)

    def test_request_slot_ttl_busy_builds_problem_detail(self) -> None:
        decision = QueueDecision(
            allowed=False,
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            retry_after=30,
            entry=None,
            reason='queue_pending_ttl',
        )
        service = SeedRunService(queue_service=_StubQueueService(decision))

        _, problem = service.request_slot(
            environment='staging',
            tenant_id=uuid4(),
            seed_run_id=None,
            now=datetime(2025, 1, 1, 12, 0, 0),
        )

        self.assertIsInstance(problem, ProblemDetail)
        assert problem
        self.assertEqual(problem.status, HTTPStatus.TOO_MANY_REQUESTS)
        self.assertEqual(problem.title, 'seed_queue_busy')
        self.assertEqual(problem.retry_after, 30)
        self.assertEqual(SeedRunService.exit_code_for(decision), 5)

    def test_exit_code_for_defaults_to_one_for_unknown_status(self) -> None:
        decision = QueueDecision(
            allowed=False,
            status_code=HTTPStatus.BAD_REQUEST,
            retry_after=None,
            entry=None,
            reason='unexpected_status',
        )

        self.assertEqual(SeedRunService.exit_code_for(decision), 1)
