from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from typing import Optional

TENANT_CANARY = 'tenant-alfa'


@dataclass(frozen=True)
class TenantRollout:
    default: bool
    tenants: Mapping[str, bool]

    def value_for(self, tenant_id: Optional[str]) -> bool:
        if tenant_id and tenant_id in self.tenants:
            return self.tenants[tenant_id]
        return self.default


DEFAULT_FLAG_ROLLOUTS: Mapping[str, TenantRollout] = {
    'foundation.fsd': TenantRollout(
        default=False,
        tenants={
            TENANT_CANARY: True,
        },
    ),
    'design-system.theming': TenantRollout(
        default=False,
        tenants={
            TENANT_CANARY: True,
        },
    ),
}


def resolve_fallback_value(flag_key: str, tenant_id: Optional[str]) -> bool:
    rollout = DEFAULT_FLAG_ROLLOUTS.get(flag_key)
    if rollout is None:
        raise KeyError(f'Flag "{flag_key}" não está definida na configuração padrão.')
    return rollout.value_for(tenant_id)


def resolve_fallback_snapshot(tenant_id: Optional[str]) -> dict[str, bool]:
    return {
        flag_key: rollout.value_for(tenant_id)
        for flag_key, rollout in DEFAULT_FLAG_ROLLOUTS.items()
    }
