"""
Multi-Factor Authentication (MFA) para IABANK.
MFA obrigatório para usuários admin e operações financeiras críticas.
"""
import io
import base64
from typing import Dict, Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
# Lazy imports para django-otp - serão importados quando necessário

def _get_django_otp_imports():
    """Lazy import para django-otp models."""
    from django_otp import match_token
    from django_otp.models import Device
    from django_otp.plugins.otp_totp.models import TOTPDevice
    from django_otp.plugins.otp_static.models import StaticDevice, StaticToken

    return {
        'match_token': match_token,
        'Device': Device,
        'TOTPDevice': TOTPDevice,
        'StaticDevice': StaticDevice,
        'StaticToken': StaticToken,
    }

import qrcode
import qrcode.image.svg

from iabank.core.logging import get_logger, log_business_event
from iabank.core.exceptions import IABANKAPIException


logger = get_logger(__name__)
User = get_user_model()


class MFARequiredException(IABANKAPIException):
    """Exception para MFA obrigatório não configurado."""

    def __init__(self, message: str = "MFA setup required"):
        super().__init__(
            detail=message,
            code="MFA_SETUP_REQUIRED",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class MFAManager:
    """
    Manager para operações de MFA.

    Features:
    - Setup de TOTP via QR Code
    - Validação de códigos MFA
    - Gerenciamento de dispositivos
    - Recovery codes estáticos
    """

    def __init__(self, user):
        self.user = user
        self.logger = get_logger(f"{self.__class__.__name__}.{user.username}")

    def is_mfa_enabled(self) -> bool:
        """
        Verifica se usuário tem MFA habilitado.

        Returns:
            bool: True se MFA configurado
        """
        otp_models = _get_django_otp_imports()
        TOTPDevice = otp_models['TOTPDevice']
        return TOTPDevice.objects.filter(
            user=self.user,
            confirmed=True,
        ).exists()

    def is_mfa_required(self) -> bool:
        """
        Verifica se MFA é obrigatório para usuário.

        Rules:
        - Admin users: sempre obrigatório
        - Staff users: obrigatório
        - Regular users: opcional

        Returns:
            bool: True se MFA obrigatório
        """
        return self.user.is_staff or self.user.is_superuser

    def setup_totp_device(self, device_name: str = "IABANK") -> Dict[str, Any]:
        """
        Configura dispositivo TOTP para usuário.

        Args:
            device_name: Nome do dispositivo

        Returns:
            dict: QR code e secret key para setup
        """
        otp_models = _get_django_otp_imports()
        TOTPDevice = otp_models['TOTPDevice']

        # Remove dispositivos não confirmados
        TOTPDevice.objects.filter(
            user=self.user,
            confirmed=False,
        ).delete()

        # Cria novo dispositivo TOTP
        device = TOTPDevice.objects.create(
            user=self.user,
            name=device_name,
            confirmed=False,
        )

        # Gera QR code
        issuer = "IABANK"
        accountname = f"{self.user.username}@{issuer}"

        # URL do TOTP conforme RFC 6238
        totp_url = device.config_url

        # Gera QR code como SVG
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_url)
        qr.make(fit=True)

        # Converte para base64 para response JSON
        img_buffer = io.BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(img_buffer, format="PNG")
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

        log_business_event(
            event_type="security",
            entity_type="user",
            entity_id=str(self.user.id),
            action="mfa_setup_started",
            tenant_id=getattr(self.user, "tenant_id", None),
            user_id=str(self.user.id),
        )

        return {
            "qr_code": f"data:image/png;base64,{img_base64}",
            "secret_key": device.key,
            "manual_entry_key": device.key,
            "device_id": device.id,
            "issuer": issuer,
            "account_name": accountname,
        }

    def verify_and_enable_totp(
        self,
        token: str,
        device_id: Optional[int] = None,
    ) -> bool:
        """
        Verifica token TOTP e habilita dispositivo.

        Args:
            token: Código TOTP de 6 dígitos
            device_id: ID do dispositivo (opcional)

        Returns:
            bool: True se verificação bem-sucedida
        """
        otp_models = _get_django_otp_imports()
        TOTPDevice = otp_models['TOTPDevice']

        try:
            # Encontra dispositivo não confirmado
            if device_id:
                device = TOTPDevice.objects.get(
                    user=self.user,
                    id=device_id,
                    confirmed=False,
                )
            else:
                device = TOTPDevice.objects.filter(
                    user=self.user,
                    confirmed=False,
                ).first()

            if not device:
                return False

            # Verifica token
            if device.verify_token(token):
                # Confirma dispositivo
                device.confirmed = True
                device.save()

                # Gera recovery codes
                self._generate_recovery_codes()

                log_business_event(
                    event_type="security",
                    entity_type="user",
                    entity_id=str(self.user.id),
                    action="mfa_enabled",
                    tenant_id=getattr(self.user, "tenant_id", None),
                    user_id=str(self.user.id),
                    device_name=device.name,
                )

                return True

        except TOTPDevice.DoesNotExist:
            pass

        log_business_event(
            event_type="security",
            entity_type="user",
            entity_id=str(self.user.id),
            action="mfa_verification_failed",
            tenant_id=getattr(self.user, "tenant_id", None),
            user_id=str(self.user.id),
        )

        return False

    def verify_token(self, token: str) -> bool:
        """
        Verifica token MFA (TOTP ou recovery code).

        Args:
            token: Token a ser verificado

        Returns:
            bool: True se token válido
        """
        otp_models = _get_django_otp_imports()
        match_token = otp_models['match_token']

        # Tenta verificar com todos os dispositivos do usuário
        device = match_token(self.user, token)

        if device:
            log_business_event(
                event_type="security",
                entity_type="user",
                entity_id=str(self.user.id),
                action="mfa_token_verified",
                tenant_id=getattr(self.user, "tenant_id", None),
                user_id=str(self.user.id),
                device_type=device.__class__.__name__,
            )
            return True

        return False

    def _generate_recovery_codes(self, count: int = 10) -> list:
        """
        Gera códigos de recovery estáticos.

        Args:
            count: Número de códigos a gerar

        Returns:
            list: Lista de recovery codes
        """
        otp_models = _get_django_otp_imports()
        StaticDevice = otp_models['StaticDevice']
        StaticToken = otp_models['StaticToken']

        # Remove device estático anterior
        StaticDevice.objects.filter(user=self.user).delete()

        # Cria novo device estático
        device = StaticDevice.objects.create(
            user=self.user,
            name="Recovery Codes",
            confirmed=True,
        )

        # Gera tokens estáticos
        recovery_codes = []
        for _ in range(count):
            token = StaticToken.random_token()
            StaticToken.objects.create(device=device, token=token)
            recovery_codes.append(token)

        self.logger.info(
            "Recovery codes generated",
            user_id=str(self.user.id),
            codes_count=count,
        )

        return recovery_codes

    def get_recovery_codes(self) -> list:
        """
        Retorna códigos de recovery não utilizados.

        Returns:
            list: Lista de códigos não utilizados
        """
        otp_models = _get_django_otp_imports()
        StaticDevice = otp_models['StaticDevice']

        try:
            device = StaticDevice.objects.get(user=self.user, name="Recovery Codes")
            return [token.token for token in device.token_set.all()]
        except StaticDevice.DoesNotExist:
            return []

    def disable_mfa(self) -> bool:
        """
        Desabilita MFA para usuário.

        Returns:
            bool: True se desabilitado com sucesso
        """
        otp_models = _get_django_otp_imports()
        Device = otp_models['Device']

        # Remove todos os dispositivos
        Device.objects.filter(user=self.user).delete()

        log_business_event(
            event_type="security",
            entity_type="user",
            entity_id=str(self.user.id),
            action="mfa_disabled",
            tenant_id=getattr(self.user, "tenant_id", None),
            user_id=str(self.user.id),
        )

        return True


# API Views para MFA

@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def setup_mfa(request: Request) -> Response:
    """
    API para setup inicial de MFA.

    Returns:
        Response: QR code e informações para configuração
    """
    manager = MFAManager(request.user)

    if manager.is_mfa_enabled():
        return Response(
            {"errors": [{"code": "MFA_ALREADY_ENABLED", "detail": "MFA já configurado"}]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    device_name = request.data.get("device_name", "IABANK TOTP")
    setup_data = manager.setup_totp_device(device_name)

    return Response({
        "data": setup_data,
        "meta": {"message": "Escaneie o QR code com seu app autenticador"},
    })


@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_mfa_setup(request: Request) -> Response:
    """
    API para verificar e confirmar setup de MFA.

    Expects:
        token: Código de 6 dígitos do app autenticador
        device_id: ID do dispositivo (opcional)

    Returns:
        Response: Confirmação de setup e recovery codes
    """
    token = request.data.get("token")
    device_id = request.data.get("device_id")

    if not token:
        return Response(
            {"errors": [{"code": "TOKEN_REQUIRED", "detail": "Token é obrigatório"}]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    manager = MFAManager(request.user)

    if manager.verify_and_enable_totp(token, device_id):
        recovery_codes = manager.get_recovery_codes()

        return Response({
            "data": {
                "mfa_enabled": True,
                "recovery_codes": recovery_codes,
            },
            "meta": {
                "message": "MFA configurado com sucesso",
                "warning": "Guarde os códigos de recovery em local seguro",
            },
        })
    else:
        return Response(
            {"errors": [{"code": "INVALID_TOKEN", "detail": "Token inválido"}]},
            status=status.HTTP_400_BAD_REQUEST,
        )


@csrf_exempt
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_mfa_token(request: Request) -> Response:
    """
    API para verificação de token MFA.

    Expects:
        token: Código TOTP ou recovery code

    Returns:
        Response: Resultado da verificação
    """
    token = request.data.get("token")

    if not token:
        return Response(
            {"errors": [{"code": "TOKEN_REQUIRED", "detail": "Token é obrigatório"}]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    manager = MFAManager(request.user)

    if manager.verify_token(token):
        return Response({
            "data": {"token_valid": True},
            "meta": {"message": "Token MFA válido"},
        })
    else:
        return Response(
            {"errors": [{"code": "INVALID_TOKEN", "detail": "Token MFA inválido"}]},
            status=status.HTTP_401_UNAUTHORIZED,
        )


def require_mfa_for_admin(user) -> None:
    """
    Enforcer para MFA obrigatório em admin users.

    Args:
        user: User instance

    Raises:
        MFARequiredException: Se MFA obrigatório e não configurado
    """
    manager = MFAManager(user)

    if manager.is_mfa_required() and not manager.is_mfa_enabled():
        raise MFARequiredException(
            "MFA é obrigatório para usuários administrativos"
        )