from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Sequence

from django.conf import settings
from django.utils import timezone

DEFAULT_REPORT_ONLY_TTL_DAYS = 30


def _ensure_aware(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.utc)
    return value


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return _ensure_aware(value)

    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        try:
            parsed = datetime.fromisoformat(candidate.replace('Z', '+00:00'))
        except ValueError:
            return None
        return _ensure_aware(parsed)

    return None


def _resolve_now(config: dict[str, object]) -> datetime:
    parsed = _parse_datetime(config.get('now'))
    if parsed is not None:
        return parsed
    return timezone.now()


def _resolve_mode(config: dict[str, object], reference: datetime) -> str:
    raw_mode = str(config.get('mode', 'auto')).lower()
    if raw_mode in {'report-only', 'enforce', 'both'}:
        return raw_mode

    ttl_raw = config.get('report_only_ttl_days', DEFAULT_REPORT_ONLY_TTL_DAYS)
    try:
        ttl_days = max(int(ttl_raw), 0)
    except (TypeError, ValueError):
        ttl_days = DEFAULT_REPORT_ONLY_TTL_DAYS

    started_at = _parse_datetime(config.get('report_only_started_at'))
    if started_at is None:
        return 'enforce'

    expires_at = started_at + timedelta(days=ttl_days)
    return 'report-only' if reference < expires_at else 'enforce'


def _coerce_values(values: object, default: list[str]) -> list[str]:
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes)):
        return default

    if isinstance(values, Sequence):
        iterable = values  # type: ignore[assignment]
    else:
        iterable = list(values)

    cleaned: List[str] = []
    for value in iterable:
        if not isinstance(value, str):
            continue
        trimmed = value.strip()
        if trimmed:
            cleaned.append(trimmed)
    return cleaned or default


def _build_directive(name: str, values: Iterable[str]) -> str:
    seen: set[str] = set()
    items: list[str] = []
    for item in values:
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        items.append(item)
    return f"{name} {' '.join(items)}"


def _apply_exceptions(
    directives: dict[str, list[str]],
    raw_exceptions: object,
    reference: datetime,
) -> None:
    if not isinstance(raw_exceptions, Iterable) or isinstance(raw_exceptions, (str, bytes)):
        return

    for entry in raw_exceptions:
        if not isinstance(entry, dict):
            continue
        directive = str(entry.get('directive', '')).strip()
        value = str(entry.get('value', '')).strip()
        if not directive or not value:
            continue

        expires_at = _parse_datetime(entry.get('expires_at'))
        if expires_at is None or expires_at <= reference:
            continue

        bucket = directives.get(directive)
        if bucket is None:
            continue

        if value not in bucket:
            bucket.append(value)


def build_csp_header(config: dict[str, object], reference: datetime | None = None) -> str:
    if reference is None:
        reference = _resolve_now(config)

    nonce = str(config.get('nonce', 'nonce-dev-fallback')).strip()
    policy = str(config.get('trusted_types_policy', 'foundation-ui')).strip() or 'foundation-ui'

    script_src = ["'self'", "'strict-dynamic'", f"'nonce-{nonce}'"]
    connect_src = _coerce_values(
        config.get('connect_src'),
        ["'self'", 'https://api.iabank.com', 'https://staging-api.iabank.com'],
    )
    style_src = _coerce_values(config.get('style_src'), ["'self'"])
    img_src = _coerce_values(config.get('img_src'), ["'self'", 'data:'])
    font_src = _coerce_values(config.get('font_src'), ["'self'"])

    directive_map = {
        'script-src': script_src,
        'connect-src': connect_src,
        'style-src': style_src,
        'img-src': img_src,
        'font-src': font_src,
    }

    _apply_exceptions(directive_map, config.get('exceptions'), reference)

    directives = [
        "default-src 'none'",
        "base-uri 'self'",
        _build_directive('script-src', directive_map['script-src']),
        _build_directive('connect-src', directive_map['connect-src']),
        _build_directive('style-src', directive_map['style-src']),
        _build_directive('img-src', directive_map['img-src']),
        _build_directive('font-src', directive_map['font-src']),
        "object-src 'none'",
        "frame-ancestors 'none'",
        "require-trusted-types-for 'script'",
        f'trusted-types {policy}',
    ]

    report_uri = config.get('report_uri')
    if report_uri:
        directives.append(f'report-uri {report_uri}')

    return '; '.join(directives)


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        config = getattr(settings, 'FOUNDATION_CSP', {})
        reference = _resolve_now(config)
        header_value = build_csp_header(config, reference=reference)
        mode = _resolve_mode(config, reference)

        if mode == 'enforce':
            response.headers.pop('Content-Security-Policy-Report-Only', None)
            response['Content-Security-Policy'] = header_value
        elif mode == 'both':
            response['Content-Security-Policy'] = header_value
            response['Content-Security-Policy-Report-Only'] = header_value
        else:
            response.headers.pop('Content-Security-Policy', None)
            response['Content-Security-Policy-Report-Only'] = header_value

        return response
