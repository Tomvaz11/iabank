from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from django.utils import timezone
from rest_framework.response import Response

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedIdempotency


@dataclass
class ResponseSnapshot:
    status: int
    body: Any
    headers: Dict[str, str]
    manifest_hash: str


@dataclass
class IdempotencyDecision:
    outcome: str  # new | replay | conflict
    entry: Optional[SeedIdempotency]
    cached_response: Optional[Response] = None


class SeedIdempotencyService:
    TTL_HOURS = 24
    _response_cache: dict[tuple[str, str, str], ResponseSnapshot] = {}

    def __init__(self, tenant_id: UUID, *, context: str = 'seed_profile_validate') -> None:
        self.tenant_id = tenant_id
        self.context = context

    @staticmethod
    def ttl_for_mode(mode: str) -> int:
        normalized = (mode or '').lower()
        if normalized in {'carga', 'load', 'dr', 'disaster_recovery'}:
            return 6
        return SeedIdempotencyService.TTL_HOURS

    def ensure_entry(
        self,
        *,
        environment: str,
        idempotency_key: str,
        manifest_hash: str,
        mode: str,
        ttl_hours: Optional[int] = None,
    ) -> IdempotencyDecision:
        now = timezone.now()
        effective_ttl = ttl_hours if ttl_hours is not None else self.ttl_for_mode(mode)
        with use_tenant(self.tenant_id):
            entry = (
                SeedIdempotency.objects.filter(environment=environment, idempotency_key=idempotency_key)
                .order_by('-created_at')
                .first()
            )

        if entry and entry.expires_at <= now:
            with use_tenant(self.tenant_id):
                entry.delete()
            entry = None

        if entry:
            if entry.manifest_hash_sha256 != manifest_hash:
                return IdempotencyDecision('conflict', entry)

            cached = self._get_cached_response(environment, idempotency_key, manifest_hash)
            return IdempotencyDecision('replay', entry, cached)

        expires_at = now + timedelta(hours=effective_ttl)
        with use_tenant(self.tenant_id):
            entry = SeedIdempotency.objects.create(
                environment=environment,
                idempotency_key=idempotency_key,
                manifest_hash_sha256=manifest_hash,
                mode=mode,
                expires_at=expires_at,
            )
        return IdempotencyDecision('new', entry)

    def cache_response(
        self,
        *,
        environment: str,
        idempotency_key: str,
        manifest_hash: str,
        response: Response,
        context: Optional[str] = None,
    ) -> None:
        snapshot = ResponseSnapshot(
            status=response.status_code,
            body=copy.deepcopy(response.data),
            headers={str(key): str(value) for key, value in response.headers.items()},
            manifest_hash=manifest_hash,
        )
        cache_key = self._cache_key(environment, idempotency_key, context=context)
        self._response_cache[cache_key] = snapshot

    def cleanup_expired(self, *, environment: Optional[str] = None) -> int:
        now = timezone.now()
        filters = {'expires_at__lte': now}
        if environment:
            filters['environment'] = environment

        with use_tenant(self.tenant_id):
            deleted, _ = SeedIdempotency.objects.filter(**filters).delete()
        return deleted

    def _get_cached_response(
        self,
        environment: str,
        idempotency_key: str,
        manifest_hash: str,
    ) -> Optional[Response]:
        snapshot = self._response_cache.get(self._cache_key(environment, idempotency_key))
        if snapshot is None or snapshot.manifest_hash != manifest_hash:
            return None

        replay = Response(copy.deepcopy(snapshot.body), status=snapshot.status)
        for header, value in snapshot.headers.items():
            replay[header] = value
        return replay

    def _cache_key(
        self,
        environment: str,
        idempotency_key: str,
        *,
        context: Optional[str] = None,
    ) -> tuple[str, str, str]:
        return (context or self.context, environment, idempotency_key)
