"""
URLs para o core module do IABANK.
Inclui endpoints de autenticação JWT e MFA.
"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from iabank.core.jwt_views import TokenObtainPairView, TokenRefreshView


def get_mfa_views():
    """Lazy import para evitar import timing issues com django-otp."""
    from iabank.core.mfa import setup_mfa, verify_mfa_setup, verify_mfa_token
    return setup_mfa, verify_mfa_setup, verify_mfa_token


@csrf_exempt
def mfa_setup_view(request):
    """Wrapper para lazy import do setup_mfa."""
    setup_mfa, _, _ = get_mfa_views()
    return setup_mfa(request)


@csrf_exempt
def mfa_verify_setup_view(request):
    """Wrapper para lazy import do verify_mfa_setup."""
    _, verify_mfa_setup, _ = get_mfa_views()
    return verify_mfa_setup(request)


@csrf_exempt
def mfa_verify_token_view(request):
    """Wrapper para lazy import do verify_mfa_token."""
    _, _, verify_mfa_token = get_mfa_views()
    return verify_mfa_token(request)


urlpatterns = [
    # JWT Authentication endpoints
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # MFA endpoints (lazy import)
    path("auth/mfa/setup/", mfa_setup_view, name="mfa_setup"),
    path("auth/mfa/verify-setup/", mfa_verify_setup_view, name="mfa_verify_setup"),
    path("auth/mfa/verify/", mfa_verify_token_view, name="mfa_verify_token"),
]