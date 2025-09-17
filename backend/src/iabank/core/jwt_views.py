"""
JWT authentication views for IABANK.
Custom responses that follow the public OpenAPI contract.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from iabank.core.logging import get_logger, log_business_event


logger = get_logger(__name__)


def _build_error(status_code: int, code: str, detail: str, field: Optional[str] = None) -> Dict[str, Any]:
    """Create a standard error payload used across the API."""
    error: Dict[str, Any] = {
        "status": str(status_code),
        "code": code,
        "detail": detail,
    }
    if field:
        error["source"] = {"field": field}
    return error


def _serialize_user(user) -> Dict[str, Any]:
    """Return a minimal public representation of the authenticated user."""
    return {
        "id": str(user.id),
        "username": getattr(user, "username", None) or getattr(user, "email", None),
        "email": getattr(user, "email", None),
        "is_active": getattr(user, "is_active", False),
        "is_staff": getattr(user, "is_staff", False),
    }


class TokenObtainPairView(APIView):
    """Authenticate a user using email/password and return JWT tokens."""

    authentication_classes: list = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request: Request, *args, **kwargs) -> Response:
        payload = request.data or {}
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password")
        tenant_domain = payload.get("tenant_domain")

        validation_errors = []
        if not email:
            validation_errors.append(
                _build_error(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "EMAIL_REQUIRED",
                    "Campo email é obrigatório.",
                    field="email",
                )
            )
        if not password:
            validation_errors.append(
                _build_error(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "PASSWORD_REQUIRED",
                    "Campo password é obrigatório.",
                    field="password",
                )
            )

        if validation_errors:
            logger.warning("Login validation failed", email=email or None, tenant_domain=tenant_domain)
            return Response({"errors": validation_errors}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        user = self._get_user_by_email(email)

        if not user or not user.check_password(password):
            logger.warning(
                "Login failed",
                email=email,
                tenant_domain=tenant_domain,
                reason="invalid_credentials",
                remote_addr=request.META.get("REMOTE_ADDR", "unknown"),
                user_agent=request.META.get("HTTP_USER_AGENT", "unknown"),
            )
            return Response(
                {
                    "errors": [
                        _build_error(
                            status.HTTP_401_UNAUTHORIZED,
                            "INVALID_CREDENTIALS",
                            "Email ou senha inválidos.",
                        )
                    ]
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not getattr(user, "is_active", True):
            logger.warning("Login failed", email=email, reason="inactive_user")
            return Response(
                {
                    "errors": [
                        _build_error(
                            status.HTTP_403_FORBIDDEN,
                            "INACTIVE_ACCOUNT",
                            "Conta inativa. Entre em contato com o administrador.",
                        )
                    ]
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh_token = RefreshToken.for_user(user)
        access_token = refresh_token.access_token
        expires_in = int(access_token.lifetime.total_seconds())

        response_data = {
            "data": {
                "access_token": str(access_token),
                "refresh_token": str(refresh_token),
                "token_type": "Bearer",
                "expires_in": expires_in,
                "user": _serialize_user(user),
            },
            "meta": {
                "message": "Authentication successful",
                "timestamp": int(timezone.now().timestamp()),
            },
        }

        logger.info(
            "Login successful",
            email=email,
            tenant_domain=tenant_domain,
            user_id=str(user.id),
        )
        log_business_event(
            event_type="security",
            entity_type="user",
            entity_id=str(user.id),
            action="login_success",
            tenant_id=str(getattr(user, "tenant_id", "")) or None,
            user_id=str(user.id),
            email=email,
        )

        return Response(response_data, status=status.HTTP_200_OK)

    @staticmethod
    def _get_user_by_email(email: str):
        User = get_user_model()
        try:
            return User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None


class TokenRefreshView(APIView):
    """Exchange a refresh token for a fresh access token."""

    authentication_classes: list = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request: Request, *args, **kwargs) -> Response:
        payload = request.data or {}
        raw_refresh = payload.get("refresh_token") or payload.get("refresh")

        if not raw_refresh:
            return Response(
                {
                    "errors": [
                        _build_error(
                            status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "REFRESH_TOKEN_REQUIRED",
                            "Campo refresh_token é obrigatório.",
                            field="refresh_token",
                        )
                    ]
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        try:
            incoming_refresh = RefreshToken(raw_refresh)
        except TokenError:
            logger.warning("Refresh token inválido", reason="token_error")
            return Response(
                {
                    "errors": [
                        _build_error(
                            status.HTTP_401_UNAUTHORIZED,
                            "INVALID_REFRESH_TOKEN",
                            "Refresh token inválido ou expirado.",
                        )
                    ]
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = self._get_user_from_token(incoming_refresh)
        if user is None:
            logger.warning("Refresh sem usuário associado")
            return Response(
                {
                    "errors": [
                        _build_error(
                            status.HTTP_401_UNAUTHORIZED,
                            "USER_NOT_FOUND",
                            "Usuário não encontrado para o token informado.",
                        )
                    ]
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        new_refresh = RefreshToken.for_user(user)
        access_token = new_refresh.access_token
        expires_in = int(access_token.lifetime.total_seconds())

        logger.info("Token refresh successful", user_id=str(user.id))
        log_business_event(
            event_type="security",
            entity_type="user",
            entity_id=str(user.id),
            action="token_refresh",
            tenant_id=str(getattr(user, "tenant_id", "")) or None,
            user_id=str(user.id),
        )

        response_data = {
            "data": {
                "access_token": str(access_token),
                "refresh_token": str(new_refresh),
                "token_type": "Bearer",
                "expires_in": expires_in,
            },
            "meta": {
                "message": "Token refreshed successfully",
                "timestamp": int(timezone.now().timestamp()),
            },
        }

        return Response(response_data, status=status.HTTP_200_OK)

    @staticmethod
    def _get_user_from_token(refresh: RefreshToken):
        user_id = refresh.get("user_id")
        if not user_id:
            return None

        User = get_user_model()
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
