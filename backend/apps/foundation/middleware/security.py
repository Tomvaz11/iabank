from __future__ import annotations

import json
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
    def _extract(entry: object) -> tuple[str, str] | None:
        if not isinstance(entry, dict):
            return None
        directive = str(entry.get('directive', '')).strip()
        value = str(entry.get('value', '')).strip()
        if not directive or not value:
            return None
        expires_at = _parse_datetime(entry.get('expires_at'))
        if expires_at is None or expires_at <= reference:
            return None
        if directive not in directives:
            return None
        return directive, value

    if not isinstance(raw_exceptions, Iterable) or isinstance(raw_exceptions, (str, bytes)):
        return

    for entry in raw_exceptions:
        parsed = _extract(entry)
        if not parsed:
            continue
        directive, value = parsed
        bucket = directives[directive]
        if value not in bucket:
            bucket.append(value)


def _resolve_report_to(config: dict[str, object]) -> dict[str, object] | None:
    group = str(config.get('report_to_group', 'csp-endpoint') or 'csp-endpoint').strip()
    max_age_raw = config.get('report_to_max_age', 86_400)
    try:
        max_age = max(int(max_age_raw), 0)
    except (TypeError, ValueError):
        max_age = 86_400

    raw_endpoints = config.get('report_to')
    endpoints = _coerce_values(raw_endpoints, [])
    if not endpoints:
        fallback_raw = config.get('report_uri')
        if fallback_raw is not None:
            fallback = str(fallback_raw).strip()
            if fallback:
                endpoints = [fallback]

    cleaned_endpoints: list[dict[str, str]] = []
    for endpoint in endpoints:
        trimmed = endpoint.strip()
        if not trimmed:
            continue
        cleaned_endpoints.append({'url': trimmed})

    if not cleaned_endpoints:
        return None

    return {
        'group': group,
        'max_age': max_age,
        'endpoints': cleaned_endpoints,
    }


def build_csp_header(
    config: dict[str, object],
    reference: datetime | None = None,
    report_to: dict[str, object] | None = None,
) -> str:
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
        _build_directive('form-action', ["'self'"]),
        "object-src 'none'",
        "frame-ancestors 'none'",
        "require-trusted-types-for 'script'",
        f'trusted-types {policy}',
    ]

    target_report = report_to if report_to is not None else _resolve_report_to(config)
    if target_report:
        directives.append(f"report-to {target_report['group']}")

    return '; '.join(directives)


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        config = getattr(settings, 'FOUNDATION_CSP', {})
        reference = _resolve_now(config)
        target_report = _resolve_report_to(config)
        header_value = build_csp_header(config, reference=reference, report_to=target_report)
        mode = _resolve_mode(config, reference)

        if target_report:
            response['Report-To'] = json.dumps(target_report)
            first_endpoint = target_report['endpoints'][0]['url']
            response['Reporting-Endpoints'] = f"{target_report['group']}=\"{first_endpoint}\""
        else:
            response.headers.pop('Report-To', None)
            response.headers.pop('Reporting-Endpoints', None)

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


class SecureHeadersMiddleware:
    """
    Acrescenta cabeçalhos de segurança que não dependem do CSP para reduzir findings DAST.
    """

    PERMISSIONS_POLICY_DEFAULT = 'camera=(), microphone=(), geolocation=(), fullscreen=(), payment=()'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Evita exposição de versão do servidor em headers default do WSGI.
        response.headers.pop('Server', None)
        response['Server'] = ''

        # Protege contra Spectre/isolamento de recursos.
        response.setdefault('Cross-Origin-Resource-Policy', 'same-origin')

        # Restringe APIs sensíveis a permissões explícitas.
        response.setdefault('Permissions-Policy', self.PERMISSIONS_POLICY_DEFAULT)

        # Evita caching de endpoints sensíveis (ex.: Problem Details, métricas/404 locais).
        if 'Cache-Control' not in response:
            response['Cache-Control'] = 'no-store'

        return response
