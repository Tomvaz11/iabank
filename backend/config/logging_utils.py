from __future__ import annotations

from typing import Any, MutableMapping, Sequence

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


def _sanitize_sequence(items: Any) -> Any:
    if isinstance(items, list):
        return [_sanitize_value(item) for item in items]
    if isinstance(items, tuple):
        return tuple(_sanitize_value(item) for item in items)
    return items


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, MutableMapping):
        return sanitize_event_dict(value)
    if isinstance(value, (list, tuple)):
        return _sanitize_sequence(value)
    return value


def sanitize_event_dict(event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    for key, value in list(event_dict.items()):
        if _should_filter(key):
            event_dict[key] = FILTERED_VALUE
            continue
        event_dict[key] = _sanitize_value(value)
    return event_dict


def structlog_pii_sanitizer(
    _: Any,
    __: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    return sanitize_event_dict(event_dict)


__all__ = ['FILTERED_VALUE', 'sanitize_event_dict', 'structlog_pii_sanitizer']
