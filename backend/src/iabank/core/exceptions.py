"""
Exception handler customizado para padronização da API.
Implementa padrões de resposta conforme OpenAPI specifications.
"""
from typing import Any, Dict, List, Optional

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from iabank.core.logging import get_logger


logger = get_logger(__name__)


class IABANKAPIException(Exception):
    """
    Exception base para APIs do IABANK.

    Segue padrão OpenAPI para responses de erro:
    {
        "errors": [
            {
                "status": "400",
                "code": "VALIDATION_ERROR",
                "detail": "Campo obrigatório",
                "source": {"field": "customer_name"}
            }
        ]
    }
    """

    def __init__(
        self,
        detail: str,
        code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        source: Optional[Dict[str, str]] = None,
    ):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        self.source = source or {}


class TenantIsolationViolation(IABANKAPIException):
    """Exception para violações de isolamento tenant."""

    def __init__(self, detail: str = "Tenant isolation violation"):
        super().__init__(
            detail=detail,
            code="TENANT_ISOLATION_VIOLATION",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class BusinessRuleViolation(IABANKAPIException):
    """Exception para violações de regras de negócio."""

    def __init__(self, detail: str, rule_code: str):
        super().__init__(
            detail=detail,
            code=f"BUSINESS_RULE_{rule_code}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class ResourceNotFound(IABANKAPIException):
    """Exception para recursos não encontrados."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            detail=f"{resource_type} with id '{resource_id}' not found",
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            source={"resource_type": resource_type, "resource_id": resource_id},
        )


def custom_exception_handler(exc, context):
    """
    Exception handler customizado para IABANK API.

    Padroniza todas as respostas de erro conforme OpenAPI spec:

    Args:
        exc: Exception instance
        context: Context do request

    Returns:
        Response: Resposta padronizada de erro
    """
    # Chama handler padrão do DRF primeiro
    response = exception_handler(exc, context)

    # Se o DRF não conseguiu tratar, tentamos tratar
    if response is None:
        response = _handle_unhandled_exceptions(exc, context)

    if response is not None:
        if isinstance(exc, (DRFValidationError, DjangoValidationError)):
            response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        # Padroniza response para formato IABANK
        response.data = _format_error_response(exc, response, context)

        # Log do erro com contexto
        _log_exception(exc, context, response.status_code)

    return response


def _handle_unhandled_exceptions(exc, context) -> Optional[Response]:
    """
    Trata exceptions não tratadas pelo DRF.

    Args:
        exc: Exception instance
        context: Request context

    Returns:
        Response ou None se não conseguir tratar
    """
    if isinstance(exc, IABANKAPIException):
        return Response(status=exc.status_code)

    if isinstance(exc, DjangoValidationError):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, Http404):
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Exceptions não tratadas retornam 500
    logger.error("Unhandled exception", exc_info=exc)
    return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _format_error_response(exc, response: Response, context) -> Dict[str, Any]:
    """
    Formata resposta de erro conforme padrão OpenAPI.

    Args:
        exc: Exception instance
        response: DRF Response
        context: Request context

    Returns:
        dict: Resposta formatada
    """
    errors = []

    if isinstance(exc, IABANKAPIException):
        errors.append({
            "status": str(exc.status_code),
            "code": exc.code,
            "detail": exc.detail,
            "source": exc.source,
        })
    elif isinstance(exc, DRFValidationError):
        errors.extend(_format_drf_validation_errors(exc, response))
    elif isinstance(exc, DjangoValidationError):
        errors.extend(_format_django_validation_errors(exc, response))
    else:
        # Erro genérico
        errors.append({
            "status": str(response.status_code),
            "code": "INTERNAL_ERROR" if response.status_code == 500 else "API_ERROR",
            "detail": _get_error_detail(exc, response),
        })

    return {"errors": errors}


def _format_drf_validation_errors(exc: DRFValidationError, response: Response) -> List[Dict[str, Any]]:
    """
    Formata erros de validação do DRF.

    Args:
        exc: DRF ValidationError
        response: Response com dados do erro

    Returns:
        List[dict]: Lista de erros formatados
    """
    errors = []

    if isinstance(response.data, dict):
        for field, messages in response.data.items():
            if isinstance(messages, list):
                for message in messages:
                    errors.append({
                        "status": str(response.status_code),
                        "code": "VALIDATION_ERROR",
                        "detail": str(message),
                        "source": {"field": field} if field != "non_field_errors" else {},
                    })
            else:
                errors.append({
                    "status": str(response.status_code),
                    "code": "VALIDATION_ERROR",
                    "detail": str(messages),
                    "source": {"field": field} if field != "non_field_errors" else {},
                })
    elif isinstance(response.data, list):
        for message in response.data:
            errors.append({
                "status": str(response.status_code),
                "code": "VALIDATION_ERROR",
                "detail": str(message),
            })

    return errors


def _format_django_validation_errors(exc: DjangoValidationError, response: Response) -> List[Dict[str, Any]]:
    """
    Formata erros de validação do Django.

    Args:
        exc: Django ValidationError
        response: Response

    Returns:
        List[dict]: Lista de erros formatados
    """
    errors = []

    if hasattr(exc, "error_dict"):
        # ValidationError com múltiplos campos
        for field, error_list in exc.error_dict.items():
            for error in error_list:
                errors.append({
                    "status": str(response.status_code),
                    "code": "VALIDATION_ERROR",
                    "detail": error.message,
                    "source": {"field": field},
                })
    elif hasattr(exc, "error_list"):
        # ValidationError com lista de erros
        for error in exc.error_list:
            errors.append({
                "status": str(response.status_code),
                "code": "VALIDATION_ERROR",
                "detail": error.message,
            })
    else:
        # ValidationError simples
        errors.append({
            "status": str(response.status_code),
            "code": "VALIDATION_ERROR",
            "detail": str(exc),
        })

    return errors


def _get_error_detail(exc, response: Response) -> str:
    """
    Extrai detalhe do erro de forma segura.

    Args:
        exc: Exception
        response: Response

    Returns:
        str: Detalhe do erro
    """
    if hasattr(response, "data") and response.data:
        if isinstance(response.data, dict):
            return response.data.get("detail", str(exc))
        elif isinstance(response.data, str):
            return response.data
        else:
            return str(response.data)

    return str(exc) if exc else "Internal server error"


def _log_exception(exc, context, status_code: int) -> None:
    """
    Log estruturado da exception com contexto.

    Args:
        exc: Exception
        context: Request context
        status_code: HTTP status code
    """
    request = context.get("request")

    log_context = {
        "exception_type": exc.__class__.__name__,
        "status_code": status_code,
    }

    if request:
        log_context.update({
            "method": request.method,
            "path": request.path,
            "user_id": str(request.user.id) if hasattr(request, "user") and request.user.is_authenticated else None,
        })

    # Log de erro baseado na severidade
    if status_code >= 500:
        logger.error("Server error", exc_info=exc, **log_context)
    elif status_code >= 400:
        logger.warning("Client error", exception_detail=str(exc), **log_context)
    else:
        logger.info("Exception handled", exception_detail=str(exc), **log_context)