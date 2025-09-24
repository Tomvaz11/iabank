"""Testes de integração para garantir configurações críticas de segurança e multi-tenancy."""

from django.conf import settings


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
