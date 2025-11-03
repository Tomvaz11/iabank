from __future__ import annotations

from typing import Dict
from typing import Optional

import pytest

from backend.apps.foundation.services.flag_gate import FlagGate
from backend.config.feature_flags import DEFAULT_FLAG_ROLLOUTS


class StubProvider:
    def __init__(self, values: Dict[str, bool]) -> None:
        self.values = values
        self.calls: list[tuple[str, str | None]] = []

    def get(self, flag_key: str, tenant_id: Optional[str], default: bool) -> bool:
        self.calls.append((flag_key, tenant_id))
        return self.values.get(flag_key, default)


@pytest.mark.django_db
class TestFlagGate:
    def test_returns_fallback_value_when_provider_not_available(self) -> None:
        gate = FlagGate()

        assert gate.is_enabled('foundation.fsd', 'tenant-alfa') is True
        assert gate.is_enabled('foundation.fsd', 'tenant-beta') is False
        assert gate.is_enabled('design-system.theming', 'tenant-alfa') is True
        assert gate.is_enabled('design-system.theming', None) is False

    def test_uses_external_provider_when_present(self) -> None:
        provider = StubProvider({'foundation.fsd': False})
        gate = FlagGate(provider=provider)

        assert gate.is_enabled('foundation.fsd', 'tenant-alfa') is False
        assert provider.calls == [('foundation.fsd', 'tenant-alfa')]

    def test_snapshot_returns_all_flags(self) -> None:
        gate = FlagGate()
        snapshot = gate.snapshot_for('tenant-alfa')

        assert set(snapshot.keys()) == set(DEFAULT_FLAG_ROLLOUTS.keys())
        assert snapshot['foundation.fsd'] is True
        assert snapshot['design-system.theming'] is True
