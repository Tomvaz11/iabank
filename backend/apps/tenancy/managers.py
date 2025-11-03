from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterable, Iterator, Optional, Union
from uuid import UUID
import uuid

from django.db import models

TenantIdentifier = Union[str, UUID]


class TenantContextError(RuntimeError):
    """Exceção lançada quando um tenant não está definido no contexto."""


_current_tenant: ContextVar[Optional[str]] = ContextVar('current_tenant_id', default=None)


def _normalize_tenant_id(value: TenantIdentifier) -> str:
    return str(value)


def _parse_tenant_id(value: TenantIdentifier) -> UUID:
    if isinstance(value, UUID):
        return value
    return uuid.UUID(str(value))


@contextmanager
def use_tenant(tenant_id: TenantIdentifier) -> Iterator[str]:
    token = _current_tenant.set(_normalize_tenant_id(tenant_id))
    try:
        yield _normalize_tenant_id(tenant_id)
    finally:
        _current_tenant.reset(token)


class TenantQuerySet(models.QuerySet):
    def for_tenant(self, tenant: TenantIdentifier) -> 'TenantQuerySet':
        return self.filter(tenant_id=_normalize_tenant_id(tenant))


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):  # type: ignore[misc]
    use_in_migrations = True

    def _require_tenant(self, tenant: Optional[TenantIdentifier] = None) -> UUID:
        if tenant is not None:
            return _parse_tenant_id(tenant)

        current = _current_tenant.get()
        if current is None:
            raise TenantContextError(
                'Tenant não definido no contexto. Use `use_tenant` para estabelecer o escopo.',
            )
        return _parse_tenant_id(current)

    def get_queryset(self) -> TenantQuerySet:  # type: ignore[override]
        tenant_id = self._require_tenant()
        return super().get_queryset().filter(tenant_id=tenant_id)

    def scoped(self, tenant: Optional[TenantIdentifier] = None) -> TenantQuerySet:
        tenant_id = self._require_tenant(tenant)
        return super().get_queryset().filter(tenant_id=tenant_id)

    def unscoped(self) -> TenantQuerySet:
        return super().get_queryset()

    def create(self, **kwargs):  # type: ignore[override]
        if 'tenant_id' not in kwargs and 'tenant' not in kwargs:
            kwargs['tenant_id'] = self._require_tenant()
        return self.unscoped().create(**kwargs)

    def bulk_create(self, objs: Iterable[models.Model], *args, **kwargs):  # type: ignore[override]
        tenant_id = self._require_tenant()
        for obj in objs:
            if getattr(obj, 'tenant_id', None) is None and getattr(obj, 'tenant', None) is None:
                setattr(obj, 'tenant_id', tenant_id)
        return self.unscoped().bulk_create(objs, *args, **kwargs)

    def update_or_create(self, defaults=None, **kwargs):  # type: ignore[override]
        if 'tenant_id' not in kwargs and 'tenant' not in kwargs:
            kwargs['tenant_id'] = self._require_tenant()
        return self.unscoped().update_or_create(defaults=defaults, **kwargs)
