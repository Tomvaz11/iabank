"""Middleware e mixins de suporte ao isolamento multi-tenant."""
import contextlib
import logging
import uuid
from contextvars import ContextVar
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connections, models
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .models import Tenant
from .logging import bind_structlog_context


logger = logging.getLogger(__name__)
_current_tenant: ContextVar[Optional[Tenant]] = ContextVar(
    "iabank_current_tenant", default=None
)
_RESERVED_SUBDOMAINS = {"www", "api", "admin"}


class TenantMiddleware(MiddlewareMixin):
    """Define contexto de tenant para cada requisicao HTTP."""

    header_name = "HTTP_X_TENANT_ID"

    def process_request(self, request):
        """Resolve o tenant da requisicao e aplica contexto."""
        try:
            identifier_or_tenant = self._extract_tenant_identifier(request)
        except ValidationError:
            return self._tenant_invalid_response()

        if identifier_or_tenant is None:
            return self._tenant_required_response()

        try:
            tenant = self._resolve_tenant(identifier_or_tenant)
        except ValidationError as exc:
            logger.warning("Tenant identifier invalid: %s", exc)
            return self._tenant_invalid_response()
        except Tenant.DoesNotExist:
            logger.warning("Tenant not found: %s", identifier_or_tenant)
            return self._tenant_not_found_response()
        except Exception as exc:  # pragma: no cover - fallback
            logger.exception("Unexpected error resolving tenant: %s", exc)
            return self._server_error_response()

        if not tenant.is_active:
            logger.info("Tenant inactive: %s", tenant.id)
            return self._tenant_inactive_response()

        request.tenant = tenant
        request.tenant_id = tenant.id
        request._tenant_context_token = _current_tenant.set(tenant)

        bind_structlog_context(tenant_id=tenant.id)
        self._set_rls_context(tenant)
        return None

    def process_response(self, request, response):
        """Limpa contexto de tenant ao final da resposta."""
        token = getattr(request, "_tenant_context_token", None)
        if token is not None:
            with contextlib.suppress(LookupError):
                _current_tenant.reset(token)
        else:
            _current_tenant.set(None)

        self._clear_rls_context()
        return response

    # ------------------------------------------------------------------
    # Tenant resolution helpers
    # ------------------------------------------------------------------

    def _extract_tenant_identifier(self, request):
        """Extrai identificador do tenant a partir de header, JWT ou subdominio."""
        header_value = request.META.get(self.header_name)
        if header_value:
            header_value = header_value.strip()
            if not header_value:
                raise ValidationError("Tenant header vazio")
            try:
                uuid.UUID(header_value)
            except ValueError as exc:
                raise ValidationError("Tenant header invalido") from exc
            return header_value

        token_value = self._extract_from_jwt(request)
        if token_value:
            try:
                uuid.UUID(str(token_value))
            except ValueError as exc:
                raise ValidationError("Tenant JWT invalido") from exc
            return str(token_value)

        tenant = self._extract_from_subdomain(request)
        if tenant:
            return tenant

        if settings.DEBUG and hasattr(settings, "DEFAULT_TENANT_ID"):
            default_id = str(settings.DEFAULT_TENANT_ID)
            try:
                uuid.UUID(default_id)
            except ValueError as exc:
                raise ValidationError("DEFAULT_TENANT_ID invalido") from exc
            return default_id

        return None

    def _extract_from_jwt(self, request) -> Optional[str]:
        """Obtem tenant_id de um token JWT se presente."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None

        try:
            from jwt import decode
            from rest_framework_simplejwt.tokens import UntypedToken

            token = auth_header.split(" ", 1)[1]
            UntypedToken(token)
            decoded = decode(token, options={"verify_signature": False})
            return decoded.get("tenant_id")
        except Exception:
            return None

    def _extract_from_subdomain(self, request) -> Optional[Tenant]:
        """Resolve tenant por subdominio ou dominio customizado."""
        host = request.get_host().split(":")[0].lower()
        if not host:
            return None

        tenant = Tenant.objects.filter(domain=host).first()
        if tenant:
            return tenant

        parts = host.split(".")
        if len(parts) < 3:
            return None

        subdomain = parts[0]
        if subdomain in _RESERVED_SUBDOMAINS:
            return None

        return Tenant.objects.filter(slug=subdomain).first()

    def _resolve_tenant(self, identifier_or_tenant):
        """Normaliza identificador e retorna instancia de Tenant."""
        if isinstance(identifier_or_tenant, Tenant):
            return identifier_or_tenant

        identifier = str(identifier_or_tenant).strip()
        if not identifier:
            raise ValidationError("Identificador de tenant vazio")

        try:
            tenant_uuid = uuid.UUID(identifier)
        except ValueError as exc:
            raise ValidationError("Tenant id invalido") from exc

        return Tenant.objects.get(id=tenant_uuid)

    # ------------------------------------------------------------------
    # Context helpers
    # ------------------------------------------------------------------

    def _set_rls_context(self, tenant: Tenant):
        """Configura contexto de RLS no PostgreSQL."""
        try:
            conn = connections["default"]
            with conn.cursor() as cursor:
                cursor.execute("SELECT set_tenant_context(%s)", [str(tenant.id)])
        except Exception as exc:  # pragma: no cover - logging auxiliar
            logger.warning("Failed to set RLS context: %s", exc)

    def _clear_rls_context(self):
        """Remove contexto de RLS ao final da requisicao."""
        try:
            conn = connections["default"]
            with conn.cursor() as cursor:
                cursor.execute("RESET iabank.current_tenant_id")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Responses helpers
    # ------------------------------------------------------------------

    def _tenant_required_response(self):
        return self._error_response(
            status=400,
            code="TENANT_REQUIRED",
            detail="Tenant identification is required. Provide X-Tenant-ID header or valid JWT token.",
        )

    def _tenant_invalid_response(self):
        return self._error_response(
            status=400,
            code="TENANT_INVALID",
            detail="Provided tenant identifier is not valid.",
        )

    def _tenant_not_found_response(self):
        return self._error_response(
            status=404,
            code="TENANT_NOT_FOUND",
            detail="The specified tenant was not found.",
        )

    def _tenant_inactive_response(self):
        return self._error_response(
            status=403,
            code="TENANT_INACTIVE",
            detail="This tenant account is inactive. Please contact support.",
        )

    def _server_error_response(self):
        return self._error_response(
            status=500,
            code="INTERNAL_ERROR",
            detail="An internal error occurred while processing tenant context.",
        )

    @staticmethod
    def _error_response(*, status: int, code: str, detail: str) -> JsonResponse:
        return JsonResponse(
            {"errors": [{"status": str(status), "code": code, "detail": detail}]},
            status=status,
        )

    @classmethod
    def get_current_tenant(cls) -> Optional[Tenant]:
        """Retorna tenant atual do contexto."""
        return _current_tenant.get()


class TenantQuerySetMixin:
    """Mixin para aplicar filtro por tenant automaticamente."""

    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = TenantMiddleware.get_current_tenant()
        if tenant and hasattr(queryset.model, "tenant_id"):
            return queryset.filter(tenant_id=tenant.id)
        return queryset


class TenantModelMixin(models.Model):
    """Mixin para definir tenant_id automaticamente ao salvar."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not getattr(self, "tenant_id", None):
            tenant = TenantMiddleware.get_current_tenant()
            if tenant is None:
                raise ValidationError("No tenant context available")
            self.tenant_id = tenant.id
        super().save(*args, **kwargs)
