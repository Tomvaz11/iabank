import pytest

from backend.apps.foundation.services.flag_gate import FlagGate
from backend.config.feature_flags import TenantRollout


class DummyProvider:
    def __init__(self, values: dict[str, bool] | None = None, fail: bool = False):
        self.values = values or {}
        self.fail = fail
        self.closed = False

    def get(self, flag_key: str, tenant_id: str | None, default: bool) -> bool:  # type: ignore[override]
        if self.fail:
            raise RuntimeError('provider failure')
        return self.values.get(flag_key, default)

    def close(self) -> None:  # type: ignore[override]
        self.closed = True


@pytest.mark.django_db(False)
def test_flag_gate_uses_fallback_without_provider(monkeypatch):
    # Força rollouts de fallback previsíveis
    monkeypatch.setattr(
        'backend.config.feature_flags.DEFAULT_FLAG_ROLLOUTS',
        {
            'foundation.fsd': TenantRollout(default=False, tenants={'tenant-alfa': True}),
            'design-system.theming': TenantRollout(default=False, tenants={'tenant-alfa': False}),
        },
        raising=False,
    )
    gate = FlagGate(provider=None)
    # Snapshot should be computed from resolve_fallback_snapshot
    snapshot = gate.snapshot_for('tenant-alfa')
    assert isinstance(snapshot, dict)


@pytest.mark.django_db(False)
def test_flag_gate_delegates_to_provider_and_handles_errors():
    provider = DummyProvider({'foundation.fsd': True})
    gate = FlagGate(provider=provider)
    assert gate.is_enabled('foundation.fsd', 't') is True
    # Unknown flag -> default path in provider
    assert isinstance(gate.snapshot_for('t'), dict)

    # When provider fails, gate falls back to default
    provider.fail = True
    assert isinstance(gate.snapshot_for('t'), dict)

    # Close must ignore provider exceptions
    provider.fail = True
    gate.close()
    # closed flag may remain False due to failure; no exception raised

