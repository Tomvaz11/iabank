"""Testes de integração para garantir configurações críticas de segurança e multi-tenancy."""

from django.conf import settings


def _normalize(values):
    return {value.lower() for value in values}


def test_tenant_middleware_ativo():
    """TenantMiddleware deve estar configurado para garantir isolamento multi-tenant."""
    assert "iabank.core.middleware.TenantMiddleware" in settings.MIDDLEWARE


def test_middleware_mfa_ativo():
    """OTPMiddleware precisa estar ativo para reforçar MFA."""
    assert "django_otp.middleware.OTPMiddleware" in settings.MIDDLEWARE


def test_flags_de_seguranca_basicas():
    """Configurações de segurança devem proteger contra ataques comuns."""
    assert settings.SECURE_BROWSER_XSS_FILTER is True
    assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.CSRF_COOKIE_HTTPONLY is True


def test_cors_headers_permite_headers_multitenant():
    """CORS deve permitir headers usados para rastreio e multi-tenant."""
    allowed_headers = _normalize(settings.CORS_ALLOW_HEADERS)
    assert {"authorization", "x-tenant-id", "x-request-id"}.issubset(allowed_headers)


def test_cors_expoe_identificadores_de_requisicao():
    """Respostas devem expor identificadores úteis para auditoria."""
    exposed_headers = _normalize(settings.CORS_EXPOSE_HEADERS)
    assert {"x-request-id", "x-tenant-id"}.issubset(exposed_headers)


def test_cors_suporta_dominios_customizados_por_regex():
    """RegEx de CORS precisa aceitar subdomínios HTTPS do IABANK."""
    assert any(
        pattern == r"^https://.*\.iabank\.com$"
        for pattern in settings.CORS_ALLOWED_ORIGIN_REGEXES
    )


def test_hsts_configurado_para_https():
    """HSTS deve estar ativo para endurecer navegação HTTPS."""
    assert settings.SECURE_HSTS_SECONDS >= 31536000
    assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
    assert settings.SECURE_HSTS_PRELOAD is True
