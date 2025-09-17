"""
URLs for the IABANK core module.
Includes MFA and auxiliary test endpoints.
"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from iabank.core.test_views import (
    setup_test_data,
    create_overdue_loan,
    create_loan_with_installments,
)


def get_mfa_views():
    """Lazy import to avoid django-otp import timing issues."""
    from iabank.core.mfa import setup_mfa, verify_mfa_setup, verify_mfa_token

    return setup_mfa, verify_mfa_setup, verify_mfa_token


@csrf_exempt
def mfa_setup_view(request):
    """Wrapper for lazy import of setup_mfa."""
    setup_mfa, _, _ = get_mfa_views()
    return setup_mfa(request)


@csrf_exempt
def mfa_verify_setup_view(request):
    """Wrapper for lazy import of verify_mfa_setup."""
    _, verify_mfa_setup, _ = get_mfa_views()
    return verify_mfa_setup(request)


@csrf_exempt
def mfa_verify_token_view(request):
    """Wrapper for lazy import of verify_mfa_token."""
    _, _, verify_mfa_token = get_mfa_views()
    return verify_mfa_token(request)


urlpatterns = [
    # MFA endpoints (lazy import)
    path("auth/mfa/setup", mfa_setup_view, name="mfa_setup"),
    path("auth/mfa/verify-setup", mfa_verify_setup_view, name="mfa_verify_setup"),
    path("auth/mfa/verify", mfa_verify_token_view, name="mfa_verify_token"),

    # Test endpoints (DEBUG only) - temporary until dedicated modules are implemented
    path("test/setup", setup_test_data, name="test_setup"),
    path("test/create-overdue-loan", create_overdue_loan, name="test_create_overdue_loan"),
    path("test/create-loan-with-installments", create_loan_with_installments, name="test_create_loan_installments"),
]
