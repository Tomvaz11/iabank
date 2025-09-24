"""
Structured logging configuration para IABANK.
ConfiguraÃ§Ã£o de structlog com contexto automÃ¡tico.
"""
import logging
import uuid
from typing import Any, Dict, Union

import structlog
from django.conf import settings
from django.http import HttpRequest


def configure_structlog() -> None:
    """
    Configura structlog para logging estruturado.

    Features:
    - Logging estruturado em JSON para produÃ§Ã£o
    - Pretty printing para desenvolvimento
    - Context automÃ¡tico (request_id, user_id, tenant_id)
    - Integration com Django logging
    """
    # ConfiguraÃ§Ã£o base do structlog
    structlog.configure(
        processors=[
            # Adiciona nome do logger
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            # Contexto customizado para IABANK
            _add_iabank_context,
            # Processamento diferente por ambiente
            _get_final_processor(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _add_iabank_context(
    logger: logging.Logger, method_name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Adiciona contexto especÃ­fico do IABANK aos logs.

    Args:
        logger: Logger instance
        method_name: Nome do mÃ©todo de logging
        event_dict: DicionÃ¡rio do evento de log

    Returns:
        event_dict atualizado com contexto IABANK
    """
    # Adiciona informaÃ§Ãµes da aplicaÃ§Ã£o
    event_dict["app"] = "iabank"
    event_dict["version"] = getattr(settings, "VERSION", "unknown")
    event_dict["environment"] = getattr(settings, "ENVIRONMENT", "unknown")

    # Request ID Ãºnico por requisiÃ§Ã£o
    if "request_id" not in event_dict:
        event_dict["request_id"] = str(uuid.uuid4())[:8]

    return event_dict


def _get_final_processor() -> Union[
    structlog.dev.ConsoleRenderer, structlog.processors.JSONRenderer
]:
    """
    Retorna processador final baseado no ambiente.

    Returns:
        Processador apropriado para o ambiente
    """
    if settings.DEBUG:
        # Desenvolvimento: output colorido e legÃ­vel
        return structlog.dev.ConsoleRenderer(colors=True)
    else:
        # ProduÃ§Ã£o: JSON estruturado
        return structlog.processors.JSONRenderer()


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Factory para loggers estruturados do IABANK.

    Args:
        name: Nome do logger (usa __name__ se nÃ£o informado)

    Returns:
        Logger configurado com contexto IABANK
    """
    return structlog.get_logger(name or __name__)





def _normalize_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza valores para contexto de logging estruturado."""
    normalized: Dict[str, Any] = {}
    for key, value in context.items():
        if value is None:
            continue
        if isinstance(value, uuid.UUID):
            normalized[key] = str(value)
        elif isinstance(value, (str, int, float, bool)):
            normalized[key] = value
        else:
            normalized[key] = str(value)
    return normalized



def bind_structlog_context(**context: Any) -> None:
    """Adiciona valores normalizados ao contexto global do structlog."""
    normalized = _normalize_context(context)
    if normalized:
        structlog.contextvars.bind_contextvars(**normalized)



def get_structlog_context() -> Dict[str, Any]:
    """Retorna uma cópia do contexto atual do structlog."""
    return dict(structlog.contextvars.get_contextvars())

class RequestLoggingMiddleware:
    """
    Middleware para adicionar contexto de request aos logs.

    Adiciona automaticamente:
    - request_id único
    - user_id (se autenticado)
    - tenant_id (se disponível)
    - request_path e método HTTP
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = get_logger(__name__)

    def __call__(self, request: HttpRequest):
        request_id = self._extract_request_id(request)
        base_context = self._build_base_context(request, request_id)

        structlog.contextvars.clear_contextvars()
        bind_structlog_context(**base_context)

        self.logger.info("Request started", **base_context)

        try:
            response = self.get_response(request)
        except Exception:
            error_context = self._snapshot_context(base_context, request)
            self.logger.exception("Request failed", **error_context)
            raise
        else:
            success_context = self._snapshot_context(base_context, request)
            if response is not None:
                response["X-Request-ID"] = request_id
                if hasattr(response, "status_code"):
                    success_context["status_code"] = response.status_code
            self.logger.info("Request completed", **success_context)
            return response
        finally:
            structlog.contextvars.clear_contextvars()

    def _extract_request_id(self, request: HttpRequest) -> str:
        headers = getattr(request, "headers", {})
        raw_request_id = headers.get("X-Request-ID")
        if raw_request_id:
            cleaned = self._sanitize_header(raw_request_id, max_length=64)
            if cleaned:
                return cleaned
        return uuid.uuid4().hex[:16]

    def _build_base_context(self, request: HttpRequest, request_id: str) -> Dict[str, Any]:
        headers = getattr(request, "headers", {})
        context: Dict[str, Any] = {
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
            "remote_addr": self._get_client_ip(request),
        }

        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            if getattr(user, "id", None) is not None:
                context["user_id"] = str(user.id)
            tenant_attr = getattr(user, "tenant_id", None)
            if tenant_attr:
                context["tenant_id"] = str(tenant_attr)

        tenant_header = headers.get("X-Tenant-ID")
        if tenant_header:
            cleaned_tenant = self._sanitize_header(tenant_header, max_length=64)
            if cleaned_tenant:
                context["tenant_id"] = cleaned_tenant

        return _normalize_context(context)

    def _snapshot_context(self, base_context: Dict[str, Any], request: HttpRequest) -> Dict[str, Any]:
        current = get_structlog_context()
        merged = {**base_context, **current}
        if "remote_addr" not in merged:
            merged["remote_addr"] = self._get_client_ip(request)
        return _normalize_context(merged)

    @staticmethod
    def _sanitize_header(value: str, *, max_length: int = 128) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            return ""
        if len(cleaned) > max_length:
            return cleaned[:max_length]
        return cleaned

    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Extrai IP do cliente considerando proxies.

        Args:
            request: Django HttpRequest

        Returns:
            IP do cliente
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR", "unknown")

def log_business_event(
    event_type: str,
    entity_type: str,
    entity_id: str,
    action: str,
    tenant_id: str = None,
    user_id: str = None,
    **extra_context
) -> None:
    """
    Log padronizado para eventos de negÃ³cio.

    Args:
        event_type: Tipo do evento (audit, business, security)
        entity_type: Tipo da entidade (customer, loan, payment)
        entity_id: ID da entidade
        action: AÃ§Ã£o executada (create, update, delete, etc)
        tenant_id: ID do tenant
        user_id: ID do usuÃ¡rio
        **extra_context: Contexto adicional
    """
    logger = get_logger("iabank.business")

    context = {
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
    }

    if tenant_id:
        context["tenant_id"] = tenant_id
    if user_id:
        context["user_id"] = user_id

    context.update(extra_context)

    logger.info(f"{entity_type.title()} {action}", **context)