from __future__ import annotations

from typing import Final

from django.http import HttpRequest, HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import path


def _dummy_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse('ok')


urlpatterns: Final = [
    path('dummy/', _dummy_view, name='dummy'),
]


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
        assert "report-uri https://csp-report.iabank.test/report" in header
        assert 'Content-Security-Policy' not in response.headers

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
