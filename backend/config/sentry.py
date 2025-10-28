from __future__ import annotations

import logging
import os
from typing import Any, MutableMapping, Sequence

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

FILTERED_VALUE = '[Filtered]'
SENSITIVE_KEYWORDS: Sequence[str] = (
    'password',
    'secret',
    'token',
    'key',
    'authorization',
    'cookie',
    'domain',
    'email',
    'cpf',
    'cnpj',
    'document',
)

_initialized = False


def _parse_rate(raw: str | None, default: float) -> float:
    try:
        parsed = float(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default
    if parsed < 0:
        return 0.0
    if parsed > 1:
        return 1.0
    return parsed


def _should_filter(key: str) -> bool:
    lowered = key.lower()
    if lowered.startswith('masked_'):
        return False
    for keyword in SENSITIVE_KEYWORDS:
        if keyword == 'token':
            if lowered == 'token' or lowered.endswith('_token') or lowered.endswith('token_id'):
                return True
            continue
        if keyword in lowered:
            return True
    return False


def _scrub_mapping(data: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    for key, value in list(data.items()):
        if _should_filter(key):
            data[key] = FILTERED_VALUE
            continue
        data[key] = _scrub_value(value)
    return data


def _scrub_sequence(items: Sequence[Any]) -> Sequence[Any]:
    if isinstance(items, list):
        for index, entry in enumerate(items):
            items[index] = _scrub_value(entry)
        return items
    return type(items)(_scrub_value(entry) for entry in items)


def _scrub_value(value: Any) -> Any:
    if isinstance(value, MutableMapping):
        return _scrub_mapping(value)
    if isinstance(value, (list, tuple)):
        return _scrub_sequence(value)
    return value


def scrub_event(event: dict[str, Any] | None) -> dict[str, Any] | None:
    if event is None:
        return None
    if isinstance(event, MutableMapping):
        return _scrub_mapping(event)
    return event


def scrub_breadcrumb(breadcrumb: dict[str, Any] | None) -> dict[str, Any] | None:
    if breadcrumb is None:
        return None
    if isinstance(breadcrumb, MutableMapping):
        return _scrub_mapping(breadcrumb)
    return breadcrumb


def init_sentry() -> bool:
    global _initialized

    dsn = os.environ.get('FOUNDATION_SENTRY_DSN')
    if not dsn:
        return False

    environment = os.environ.get('FOUNDATION_SENTRY_ENVIRONMENT', 'local')
    release = os.environ.get('FOUNDATION_SENTRY_RELEASE')
    traces_rate = _parse_rate(os.environ.get('FOUNDATION_SENTRY_TRACES_SAMPLE_RATE'), 0.2)
    profiles_rate = _parse_rate(os.environ.get('FOUNDATION_SENTRY_PROFILES_SAMPLE_RATE'), 0.0)

    if _initialized:
        return True

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        traces_sample_rate=traces_rate,
        profiles_sample_rate=profiles_rate,
        send_default_pii=False,
        before_send=lambda event, hint: scrub_event(event),
        before_breadcrumb=lambda crumb, hint: scrub_breadcrumb(crumb),
    )

    _initialized = True
    return True


__all__ = ['init_sentry', 'scrub_event', 'scrub_breadcrumb']
