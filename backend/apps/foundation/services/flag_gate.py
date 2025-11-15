from __future__ import annotations

from dataclasses import dataclass
import structlog
from typing import Dict
from typing import Optional
from typing import Protocol
from typing import runtime_checkable

from backend.config.feature_flags import DEFAULT_FLAG_ROLLOUTS
from backend.config.feature_flags import resolve_fallback_snapshot
from backend.config.feature_flags import resolve_fallback_value


@runtime_checkable
class FlagProvider(Protocol):
    def get(self, flag_key: str, tenant_id: Optional[str], default: bool) -> bool: ...

    def close(self) -> None: ...


@dataclass
class FlagGate:
    provider: Optional[FlagProvider] = None
    _logger = structlog.get_logger('backend.apps.foundation.flags')

    def is_enabled(self, flag_key: str, tenant_id: Optional[str]) -> bool:
        default_value = resolve_fallback_value(flag_key, tenant_id)

        if self.provider is None:
            return default_value

        try:
            return bool(self.provider.get(flag_key, tenant_id, default_value))
        except Exception:
            return default_value

    def snapshot_for(self, tenant_id: Optional[str]) -> Dict[str, bool]:
        snapshot = resolve_fallback_snapshot(tenant_id)

        if self.provider is None:
            return snapshot

        overrides: Dict[str, bool] = {}
        for flag_key in DEFAULT_FLAG_ROLLOUTS.keys():
            overrides[flag_key] = self.is_enabled(flag_key, tenant_id)

        return overrides

    def close(self) -> None:
        if self.provider and hasattr(self.provider, 'close'):
            try:
                self.provider.close()
            except Exception:
                # Evita falhar no shutdown mas registra para observabilidade/SAST
                self._logger.warning("flag_provider_close_failed", exc_info=True)
