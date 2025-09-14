"""
Structured logging configuration para IABANK.
Configuração de structlog com contexto automático.
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
    - Logging estruturado em JSON para produção
    - Pretty printing para desenvolvimento
    - Context automático (request_id, user_id, tenant_id)
    - Integration com Django logging
    """
    # Configuração base do structlog
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
    Adiciona contexto específico do IABANK aos logs.

    Args:
        logger: Logger instance
        method_name: Nome do método de logging
        event_dict: Dicionário do evento de log

    Returns:
        event_dict atualizado com contexto IABANK
    """
    # Adiciona informações da aplicação
    event_dict["app"] = "iabank"
    event_dict["version"] = getattr(settings, "VERSION", "unknown")
    event_dict["environment"] = getattr(settings, "ENVIRONMENT", "unknown")

    # Request ID único por requisição
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
        # Desenvolvimento: output colorido e legível
        return structlog.dev.ConsoleRenderer(colors=True)
    else:
        # Produção: JSON estruturado
        return structlog.processors.JSONRenderer()


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Factory para loggers estruturados do IABANK.

    Args:
        name: Nome do logger (usa __name__ se não informado)

    Returns:
        Logger configurado com contexto IABANK
    """
    return structlog.get_logger(name or __name__)


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
        # Gera request_id único
        request_id = str(uuid.uuid4())[:8]

        # Contexto base
        context = {
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
            "remote_addr": self._get_client_ip(request),
        }

        # Adiciona user_id se autenticado
        if hasattr(request, "user") and request.user.is_authenticated:
            context["user_id"] = str(request.user.id)

            # Adiciona tenant_id se disponível
            if hasattr(request.user, "tenant_id"):
                context["tenant_id"] = str(request.user.tenant_id)

        # Adiciona tenant_id do header X-Tenant-ID
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            context["tenant_id"] = tenant_header

        # Bind contexto aos logs desta request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(**context)

        # Log início da request
        self.logger.info(
            "Request started",
            **context
        )

        response = self.get_response(request)

        # Log fim da request
        self.logger.info(
            "Request completed",
            status_code=response.status_code,
            **context
        )

        return response

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
    Log padronizado para eventos de negócio.

    Args:
        event_type: Tipo do evento (audit, business, security)
        entity_type: Tipo da entidade (customer, loan, payment)
        entity_id: ID da entidade
        action: Ação executada (create, update, delete, etc)
        tenant_id: ID do tenant
        user_id: ID do usuário
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