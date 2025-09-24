"""Tests para utilidades de logging estruturado do IABANK."""
from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

from iabank.core.logging import RequestLoggingMiddleware


def _build_request(*, request_id: str, tenant_id: str, user_id: str) -> HttpRequest:
    """Helper para construir HttpRequest de teste com contexto básico."""
    request = HttpRequest()
    request.method = "POST"
    request.path = "/api/v1/test/"
    request.META["HTTP_X_REQUEST_ID"] = request_id
    request.META["HTTP_X_TENANT_ID"] = tenant_id
    request.META["REMOTE_ADDR"] = "127.0.0.1"
    request.user = SimpleNamespace(
        is_authenticated=True,
        id=user_id,
        tenant_id=tenant_id,
    )
    return request


def test_request_logging_middleware_binds_context_and_sets_response_header():
    """RequestLoggingMiddleware deve propagar contexto e header de request."""
    get_response = MagicMock(return_value=HttpResponse(status=HTTPStatus.OK))
    middleware = RequestLoggingMiddleware(get_response)

    tenant_id = str(uuid4())
    user_id = str(uuid4())
    request_id = "req-12345abc"
    request = _build_request(request_id=request_id, tenant_id=tenant_id, user_id=user_id)

    middleware.logger = MagicMock()

    with patch(
        "iabank.core.logging.structlog.contextvars.clear_contextvars"
    ) as mock_clear, patch(
        "iabank.core.logging.structlog.contextvars.bind_contextvars"
    ) as mock_bind:
        response = middleware(request)

    # clear_contextvars deve ser chamado no início e no fim da request
    assert mock_clear.call_count == 2

    # bind_contextvars deve receber contexto completo
    mock_bind.assert_called_once()
    bound_kwargs = mock_bind.call_args.kwargs
    assert bound_kwargs["request_id"] == request_id
    assert bound_kwargs["tenant_id"] == tenant_id
    assert bound_kwargs["user_id"] == user_id
    assert bound_kwargs["method"] == "POST"
    assert bound_kwargs["path"] == "/api/v1/test/"

    # Response deve carregar header X-Request-ID
    assert response["X-Request-ID"] == request_id

    # Middleware deve registrar início e fim da request com contexto
    assert middleware.logger.info.call_count == 2
    first_call = middleware.logger.info.call_args_list[0]
    assert first_call.args[0] == "Request started"
    assert first_call.kwargs["request_id"] == request_id
    assert first_call.kwargs["tenant_id"] == tenant_id
    assert first_call.kwargs["user_id"] == user_id

    second_call = middleware.logger.info.call_args_list[1]
    assert second_call.args[0] == "Request completed"
    assert second_call.kwargs["status_code"] == HTTPStatus.OK
    assert second_call.kwargs["request_id"] == request_id

    # get_response deve ser chamado uma vez
    get_response.assert_called_once_with(request)
