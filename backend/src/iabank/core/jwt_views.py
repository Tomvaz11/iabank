"""
JWT Authentication views para IABANK.
Customização das views de token do SimpleJWT.
"""
from typing import Dict, Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenObtainPairView as BaseTokenObtainPairView,
    TokenRefreshView as BaseTokenRefreshView,
)
from rest_framework_simplejwt.tokens import RefreshToken

from iabank.core.logging import get_logger, log_business_event


logger = get_logger(__name__)


class TokenObtainPairView(BaseTokenObtainPairView):
    """
    View customizada para obter tokens JWT.

    Features:
    - Logging estruturado de tentativas de login
    - Resposta padronizada conforme OpenAPI
    - Context adicional para auditoria
    """

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Autentica usuário e retorna access + refresh tokens.

        Args:
            request: HTTP request com credenciais

        Returns:
            Response: Tokens JWT ou erro de autenticação
        """
        # Log tentativa de login
        username = request.data.get("username", "unknown")
        logger.info(
            "Login attempt",
            username=username,
            user_agent=request.META.get("HTTP_USER_AGENT", "unknown"),
            remote_addr=request.META.get("REMOTE_ADDR", "unknown"),
        )

        # Chama implementação base do SimpleJWT
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            # Login bem-sucedido - log de auditoria
            user = self.get_user_from_response(response)
            if user:
                log_business_event(
                    event_type="security",
                    entity_type="user",
                    entity_id=str(user.id),
                    action="login_success",
                    tenant_id=getattr(user, "tenant_id", None),
                    user_id=str(user.id),
                    username=username,
                )

            # Padroniza resposta conforme API standard
            response.data = self._format_success_response(response.data)

        else:
            # Login falhou - log de segurança
            logger.warning(
                "Login failed",
                username=username,
                status_code=response.status_code,
                user_agent=request.META.get("HTTP_USER_AGENT", "unknown"),
                remote_addr=request.META.get("REMOTE_ADDR", "unknown"),
            )

        return response

    def get_user_from_response(self, response: Response):
        """
        Extrai user do token para auditoria.

        Args:
            response: Response com tokens

        Returns:
            User instance ou None
        """
        try:
            access_token = response.data.get("access")
            if access_token:
                from rest_framework_simplejwt.tokens import UntypedToken
                from rest_framework_simplejwt.authentication import JWTAuthentication
                from django.contrib.auth import get_user_model

                # Decodifica token para obter user_id
                untyped_token = UntypedToken(access_token)
                user_id = untyped_token.get("user_id")

                if user_id:
                    User = get_user_model()
                    return User.objects.get(id=user_id)

        except Exception as e:
            logger.error("Error extracting user from token", error=str(e))

        return None

    def _format_success_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formata resposta de sucesso conforme padrão API.

        Args:
            data: Dados originais do SimpleJWT

        Returns:
            dict: Resposta formatada
        """
        return {
            "data": {
                "access_token": data["access"],
                "refresh_token": data["refresh"],
                "token_type": "Bearer",
                "expires_in": 900,  # 15 minutos em segundos
            },
            "meta": {
                "message": "Authentication successful",
                "timestamp": self.get_current_timestamp(),
            },
        }

    def get_current_timestamp(self) -> int:
        """Retorna timestamp atual."""
        import time
        return int(time.time())


class TokenRefreshView(BaseTokenRefreshView):
    """
    View customizada para refresh de tokens JWT.

    Features:
    - Logging de refresh de tokens
    - Resposta padronizada
    - Rotação automática de refresh tokens
    """

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Renova access token usando refresh token.

        Args:
            request: HTTP request com refresh token

        Returns:
            Response: Novos tokens ou erro
        """
        # Log tentativa de refresh
        refresh_token = request.data.get("refresh")
        user_info = self._get_user_from_refresh_token(refresh_token)

        logger.info(
            "Token refresh attempt",
            user_id=user_info.get("user_id") if user_info else None,
            tenant_id=user_info.get("tenant_id") if user_info else None,
        )

        # Chama implementação base
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            # Refresh bem-sucedido
            if user_info:
                log_business_event(
                    event_type="security",
                    entity_type="user",
                    entity_id=user_info["user_id"],
                    action="token_refresh",
                    tenant_id=user_info.get("tenant_id"),
                    user_id=user_info["user_id"],
                )

            # Padroniza resposta
            response.data = self._format_refresh_response(response.data)

        else:
            # Refresh falhou
            logger.warning(
                "Token refresh failed",
                status_code=response.status_code,
                user_id=user_info.get("user_id") if user_info else None,
            )

        return response

    def _get_user_from_refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Extrai informações do usuário do refresh token.

        Args:
            refresh_token: Token JWT

        Returns:
            dict: Informações do usuário
        """
        try:
            if refresh_token:
                token = RefreshToken(refresh_token)
                user_id = token.get("user_id")

                if user_id:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    user = User.objects.get(id=user_id)

                    return {
                        "user_id": str(user.id),
                        "tenant_id": str(getattr(user, "tenant_id", None)),
                        "username": user.username,
                    }

        except Exception as e:
            logger.error("Error extracting user from refresh token", error=str(e))

        return {}

    def _format_refresh_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formata resposta de refresh conforme padrão API.

        Args:
            data: Dados originais do SimpleJWT

        Returns:
            dict: Resposta formatada
        """
        response_data = {
            "data": {
                "access_token": data["access"],
                "token_type": "Bearer",
                "expires_in": 900,  # 15 minutos
            },
            "meta": {
                "message": "Token refreshed successfully",
                "timestamp": int(__import__("time").time()),
            },
        }

        # Inclui novo refresh token se rotacionado
        if "refresh" in data:
            response_data["data"]["refresh_token"] = data["refresh"]

        return response_data