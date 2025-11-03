from __future__ import annotations

from dataclasses import dataclass

from django.core.cache import cache


IDEMPOTENCY_TTL_SECONDS = 86400


@dataclass(slots=True)
class ScaffoldIdempotencyScope:
    tenant_id: str
    feature_slug: str

    def cache_key(self) -> str:
        return f'foundation:scaffold:idempotency:{self.tenant_id}:{self.feature_slug}'


class ScaffoldIdempotencyRegistry:
    ttl_seconds: int = IDEMPOTENCY_TTL_SECONDS

    def __init__(self) -> None:
        self._cache = cache

    def _cache_key(self, scope: ScaffoldIdempotencyScope) -> str:
        return scope.cache_key()

    def should_block(self, scope: ScaffoldIdempotencyScope, idempotency_key: str) -> bool:
        """
        Returns True when another Idempotency-Key is already registered for the same scope.
        """
        cached = self._cache.get(self._cache_key(scope))
        if cached is None:
            return False
        return cached != idempotency_key

    def remember(self, scope: ScaffoldIdempotencyScope, idempotency_key: str) -> None:
        """
        Stores the Idempotency-Key for the provided scope. Subsequent calls refresh the TTL.
        """
        cache_key = self._cache_key(scope)
        self._cache.set(cache_key, idempotency_key, timeout=self.ttl_seconds)

