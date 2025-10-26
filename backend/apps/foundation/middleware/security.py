from __future__ import annotations

from typing import Iterable, List, Sequence

from django.conf import settings


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
    items = [item for item in values if item]
    return f"{name} {' '.join(items)}"


def build_csp_header(config: dict[str, object]) -> str:
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

    directives = [
        "default-src 'none'",
        "base-uri 'self'",
        _build_directive('script-src', script_src),
        _build_directive('connect-src', connect_src),
        _build_directive('style-src', style_src),
        _build_directive('img-src', img_src),
        _build_directive('font-src', font_src),
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
        header_value = build_csp_header(config)
        mode = str(config.get('mode', 'report-only')).lower()

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
