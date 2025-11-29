from __future__ import annotations

import json
from typing import Final

from django.http import HttpRequest, HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import path


def _dummy_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse('ok')


urlpatterns: Final = [
    path('dummy/', _dummy_view, name='dummy'),
]


def _extract_directive(header: str, name: str) -> str:
    parts = [part.strip() for part in header.split(';')]
    for part in parts:
        if part.startswith(f'{name} '):
            return part
    return ''


@override_settings(ROOT_URLCONF='backend.apps.foundation.tests.test_csp_middleware')
class ContentSecurityPolicyMiddlewareTest(SimpleTestCase):
    def test_aplica_csp_report_only_com_nonce_e_trusted_types(self) -> None:
        with override_settings(
            FOUNDATION_CSP={
                'mode': 'report-only',
                'nonce': 'dev-nonce',
                'trusted_types_policy': 'foundation-ui',
                'report_uri': 'https://csp-report.iabank.test/report',
                'connect_src': ["'self'", 'https://api.iabank.test'],
                'style_src': ["'self'"],
                'img_src': ["'self'", 'data:'],
                'font_src': ["'self'"],
            },
        ):
            response = self.client.get('/dummy/')

        header = response.headers.get('Content-Security-Policy-Report-Only')
        assert header is not None
        assert "default-src 'none'" in header
        assert "script-src 'self' 'strict-dynamic' 'nonce-dev-nonce'" in header
        assert "connect-src 'self' https://api.iabank.test" in header
        assert "img-src 'self' data:" in header
        assert "trusted-types foundation-ui" in header
        assert "report-to csp-endpoint" in header
        assert 'report-uri' not in header
        assert 'Content-Security-Policy' not in response.headers

        report_to_raw = response.headers.get('Report-To')
        assert report_to_raw is not None
        parsed = json.loads(report_to_raw)
        assert parsed == {
            'group': 'csp-endpoint',
            'max_age': 86_400,
            'endpoints': [{'url': 'https://csp-report.iabank.test/report'}],
        }
        assert (
            response.headers.get('Reporting-Endpoints')
            == 'csp-endpoint="https://csp-report.iabank.test/report"'
        )

    def test_modo_enforce_move_para_cabecalho_principal(self) -> None:
        with override_settings(
            FOUNDATION_CSP={
                'mode': 'enforce',
                'nonce': 'prod-nonce',
                'trusted_types_policy': 'foundation-ui',
                'report_uri': None,
                'connect_src': ["'self'"],
                'style_src': ["'self'"],
                'img_src': ["'self'"],
                'font_src': ["'self'"],
            },
        ):
            response = self.client.get('/dummy/')

        header = response.headers.get('Content-Security-Policy')
        assert header is not None
        assert "script-src 'self' 'strict-dynamic' 'nonce-prod-nonce'" in header
        assert 'Content-Security-Policy-Report-Only' not in response.headers
        assert 'Report-To' not in response.headers
        assert 'Reporting-Endpoints' not in response.headers

    def test_modo_auto_fica_em_report_only_antes_do_prazo(self) -> None:
        with override_settings(
            FOUNDATION_CSP={
                'mode': 'auto',
                'now': '2025-10-10T00:00:00Z',
                'report_only_started_at': '2025-10-01T00:00:00Z',
                'report_only_ttl_days': 30,
                'nonce': 'dev-nonce',
                'trusted_types_policy': 'foundation-ui',
                'report_uri': None,
                'connect_src': ["'self'", 'https://api.iabank.test'],
                'style_src': ["'self'"],
                'img_src': ["'self'", 'data:'],
                'font_src': ["'self'"],
            },
        ):
            response = self.client.get('/dummy/')

        header = response.headers.get('Content-Security-Policy-Report-Only')
        assert header is not None
        assert "script-src 'self' 'strict-dynamic' 'nonce-dev-nonce'" in header
        assert 'Content-Security-Policy' not in response.headers

    def test_modo_auto_ativa_enforce_apos_expiracao(self) -> None:
        with override_settings(
            FOUNDATION_CSP={
                'mode': 'auto',
                'now': '2025-11-15T00:00:00Z',
                'report_only_started_at': '2025-10-01T00:00:00Z',
                'report_only_ttl_days': 30,
                'nonce': 'dev-nonce',
                'trusted_types_policy': 'foundation-ui',
                'report_uri': None,
                'connect_src': ["'self'", 'https://api.iabank.test'],
                'style_src': ["'self'"],
                'img_src': ["'self'", 'data:'],
                'font_src': ["'self'"],
            },
        ):
            response = self.client.get('/dummy/')

        header = response.headers.get('Content-Security-Policy')
        assert header is not None
        assert "script-src 'self' 'strict-dynamic' 'nonce-dev-nonce'" in header
        assert 'Content-Security-Policy-Report-Only' not in response.headers

    def test_excecoes_com_ttl_expirado_sao_ignoradas(self) -> None:
        with override_settings(
            FOUNDATION_CSP={
                'mode': 'enforce',
                'now': '2025-11-05T00:00:00Z',
                'nonce': 'prod-nonce',
                'trusted_types_policy': 'foundation-ui',
                'report_uri': None,
                'connect_src': ["'self'", 'https://api.iabank.test'],
                'style_src': ["'self'"],
                'img_src': ["'self'", 'data:'],
                'font_src': ["'self'"],
                'exceptions': [
                    {
                        'directive': 'connect-src',
                        'value': 'https://temporary.iabank.test',
                        'expires_at': '2025-10-01T00:00:00Z',
                    },
                    {
                        'directive': 'connect-src',
                        'value': 'https://analytics.iabank.test',
                        'expires_at': '2025-12-01T00:00:00Z',
                    },
                    {
                        'directive': 'img-src',
                        'value': 'https://images.iabank.test',
                        'expires_at': '2025-11-20T00:00:00Z',
                    },
                ],
            },
        ):
            response = self.client.get('/dummy/')

        header = response.headers.get('Content-Security-Policy')
        assert header is not None

        connect_src = _extract_directive(header, 'connect-src')
        assert 'https://analytics.iabank.test' in connect_src
        assert 'https://temporary.iabank.test' not in connect_src

        img_src = _extract_directive(header, 'img-src')
        assert 'https://images.iabank.test' in img_src
