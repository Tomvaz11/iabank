from __future__ import annotations

from types import SimpleNamespace

from backend import celery as celery_module
from backend.apps.tenancy import tasks as seed_tasks


def test_dispatch_baseline_uses_request_routing_when_present() -> None:
    fake_self = SimpleNamespace(request=SimpleNamespace(delivery_info={'routing_key': 'seed_data.default'}))
    result = seed_tasks.dispatch_baseline.__wrapped__.__func__(fake_self, seed_run_id='run-1', tenant_id='tenant-1')

    assert result['queue'] == 'seed_data.default'
    assert result['seed_run_id'] == 'run-1'


def test_dispatch_load_dr_defaults_queue_without_request() -> None:
    result = seed_tasks.dispatch_load_dr.__wrapped__.__func__(SimpleNamespace(), seed_run_id='run-2', tenant_id='tenant-2')

    assert result['queue'] == 'seed_data.load_dr'
    assert result['seed_run_id'] == 'run-2'


def test_handle_dlq_logs_reason_and_queue() -> None:
    fake_self = SimpleNamespace(request=SimpleNamespace(delivery_info={'routing_key': 'seed_data.dlq'}))
    result = seed_tasks.handle_dlq.__wrapped__.__func__(
        fake_self,
        seed_run_id='run-3',
        tenant_id='tenant-3',
        reason='too_many_retries',
    )

    assert result['queue'] == 'seed_data.dlq'
    assert result['reason'] == 'too_many_retries'


def test_celery_healthcheck_returns_ok() -> None:
    assert celery_module.healthcheck() == 'ok'
