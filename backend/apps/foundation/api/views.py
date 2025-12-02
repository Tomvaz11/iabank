from __future__ import annotations

import hashlib
import json
import time
from typing import Any
from uuid import UUID
import uuid

from django.core.cache import cache
from django.core.paginator import EmptyPage, Paginator
from django.db import connection, models
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from backend.apps.foundation.idempotency import (
    ScaffoldIdempotencyRegistry,
    ScaffoldIdempotencyScope,
)
from backend.apps.foundation.serializers import (
    DesignSystemStorySerializer,
    FeatureScaffoldRequestSerializer,
    FeatureTemplateRegistrationSerializer,
    SuccessMetricSerializer,
    TenantThemeSerializer,
)
from backend.apps.foundation.services.scaffold_registrar import ScaffoldRegistrar
from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import Tenant, TenantThemeToken
from backend.apps.foundation.models import DesignSystemStory, FeatureTemplateMetric
from ratelimit.decorators import ratelimit

PROBLEM_TYPE_BASE = 'https://iabank.local/problems/foundation'


def _update_rate_limit(cache_key: str, *, limit: int, window: int, increment: bool) -> dict[str, str]:
    now = int(time.time())
    data = cache.get(cache_key)
    if not isinstance(data, dict) or 'count' not in data or 'window_start' not in data:
        data = {'count': 0, 'window_start': now}

    elapsed = now - int(data['window_start'])
    if elapsed >= window:
        data = {'count': 0, 'window_start': now}
        elapsed = 0

    if increment:
        data['count'] = int(data['count']) + 1

    remaining = max(0, limit - int(data['count']))
    reset = window if not increment else max(1, window - elapsed)

    cache.set(cache_key, data, timeout=reset)

    return {
        'RateLimit-Limit': f'{limit};w={window}',
        'RateLimit-Remaining': str(remaining),
        'RateLimit-Reset': str(reset),
    }


# Helpers para reduzir complexidade ciclomática em endpoints
def _problem_detail_response(
    request: HttpRequest,
    *,
    status_code: int,
    title: str,
    detail: str,
    type_suffix: str,
    extra: dict[str, Any] | None = None,
) -> Response:
    body: dict[str, Any] = {
        'type': f'{PROBLEM_TYPE_BASE}/{type_suffix}',
        'title': title,
        'status': status_code,
        'detail': detail,
        'instance': request.get_full_path(),
    }
    if extra:
        body.update(extra)
    return Response(body, status=status_code)


def _invalid_params_from_validation_error(error: ValidationError) -> list[dict[str, str]]:
    invalid: list[dict[str, str]] = []
    detail = error.detail

    if isinstance(detail, dict):
        for field, reasons in detail.items():
            if isinstance(reasons, (list, tuple)):
                reason_text = '; '.join([str(reason) for reason in reasons])
            else:
                reason_text = str(reasons)
            invalid.append({'name': str(field), 'reason': reason_text})
    elif isinstance(detail, list):
        for idx, item in enumerate(detail):
            invalid.append({'name': f'item[{idx}]', 'reason': str(item)})
    else:
        invalid.append({'name': 'non_field_errors', 'reason': str(detail)})
    return invalid


def _validation_problem_response(request: HttpRequest, exc: ValidationError) -> Response:
    return _problem_detail_response(
        request,
        status_code=status.HTTP_400_BAD_REQUEST,
        title='invalid_request',
        detail='Payload inválido.',
        type_suffix='validation',
        extra={'invalidParams': _invalid_params_from_validation_error(exc)},
    )


def _parse_pagination(request: HttpRequest) -> tuple[int, int] | Response:
    try:
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 25))
    except ValueError:
        return _problem_detail_response(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            title='invalid_pagination',
            detail='Parâmetros de paginação inválidos.',
            type_suffix='pagination',
            extra={
                'invalidParams': [
                    {'name': 'page', 'reason': 'Use inteiros positivos.'},
                    {'name': 'page_size', 'reason': 'Use inteiros positivos.'},
                ]
            },
        )
    if page < 1 or page_size < 1 or page_size > 100:
        return _problem_detail_response(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            title='pagination_out_of_range',
            detail='Parâmetros de paginação fora do intervalo permitido.',
            type_suffix='pagination',
            extra={
                'invalidParams': [
                    {
                        'name': 'page_size',
                        'reason': 'Use valores entre 1 e 100.',
                    }
                ]
            },
        )
    return page, page_size


def _parse_optional_tenant_header(request: HttpRequest, header_value: str | None) -> UUID | None | Response:
    if not header_value:
        return None
    try:
        return uuid.UUID(header_value)
    except ValueError:
        return _problem_detail_response(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            title='invalid_tenant_header',
            detail='Cabeçalho X-Tenant-Id inválido.',
            type_suffix='tenant-header',
            extra={'invalidParams': [{'name': 'X-Tenant-Id', 'reason': 'Use um UUID válido ou omita o cabeçalho.'}]},
        )


def _apply_story_filters(queryset, tenant_filter: UUID | None, component_id: str | None, tag: str | None):
    if tenant_filter:
        queryset = queryset.filter(models.Q(tenant_id=tenant_filter) | models.Q(tenant__isnull=True))
    if component_id:
        queryset = queryset.filter(component_id=component_id)
    if tag:
        if connection.features.supports_json_field_contains:
            queryset = queryset.filter(tags__contains=[tag])
        else:
            queryset = queryset.filter(tags__icontains=tag)
    return queryset


def _paginate_and_serialize(queryset, page: int, page_size: int) -> tuple[list[dict[str, Any]], int, int, int]:
    paginator = Paginator(queryset, page_size)
    if paginator.count == 0:
        return [], page, 0, 0
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    serialized = DesignSystemStorySerializer(page_obj.object_list, many=True).data
    return serialized, page_obj.number, paginator.num_pages, paginator.count


def _compute_etag_for_payload(payload: dict[str, Any]) -> str:
    etag_source = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return f'"{hashlib.sha256(etag_source).hexdigest()}"'


def _respond_not_modified_if_needed(request: HttpRequest, etag_value: str) -> Response | None:
    if_none_match = request.headers.get('If-None-Match')
    if not if_none_match:
        return None
    requested = {token.strip() for token in if_none_match.split(',') if token.strip()}
    if '*' in requested or etag_value in requested:
        not_modified = Response(status=status.HTTP_304_NOT_MODIFIED)
        not_modified['ETag'] = etag_value
        return not_modified
    return None


def _precondition_response_if_needed(
    request: HttpRequest,
    *,
    idempotency_key: str,
    etag_value: str,
    location: str,
) -> Response | None:
    raw_if_none_match = request.headers.get('If-None-Match')
    if not raw_if_none_match:
        return None
    requested_etags = {token.strip() for token in raw_if_none_match.split(',') if token.strip()}
    if '*' in requested_etags:
        precondition = _problem_detail_response(
            request,
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            title='precondition_failed',
            detail='Registro de scaffolding já existe para esta feature.',
            type_suffix='precondition',
            extra={'idempotencyKey': idempotency_key},
        )
        precondition['Idempotency-Key'] = idempotency_key
        precondition['ETag'] = etag_value
        precondition['Location'] = location
        return precondition
    if etag_value in requested_etags:
        not_modified = Response(status=status.HTTP_304_NOT_MODIFIED)
        not_modified['Idempotency-Key'] = idempotency_key
        not_modified['ETag'] = etag_value
        not_modified['Location'] = location
        return not_modified
    return None


def _validate_required_tenant_header(request: HttpRequest, expected_tenant_id: str) -> Response | None:
    header_value = request.headers.get('X-Tenant-Id')
    if header_value == expected_tenant_id:
        return None
    return _problem_detail_response(
        request,
        status_code=status.HTTP_400_BAD_REQUEST,
        title='tenant_header_mismatch',
        detail='Cabeçalho X-Tenant-Id inválido ou ausente.',
        type_suffix='tenant-header',
        extra={'invalidParams': [{'name': 'X-Tenant-Id', 'reason': 'Forneça o UUID do tenant correspondente.'}]},
    )


@method_decorator(
    ratelimit(
        key='header:x-tenant-id',
        rate='30/m',
        method='POST',
        block=False,
    ),
    name='post',
)
class RegisterFeatureScaffoldView(APIView):
    def post(self, request: HttpRequest, tenant_id: UUID, *args: Any, **kwargs: Any) -> Response:
        rate_limit = 30
        window_seconds = 60
        tenant_uuid = str(tenant_id)
        cache_key = f'foundation:scaffold:ratelimit:{tenant_uuid}'

        # Rate limit (não bloquear setup de headers de limite ao exceder)
        if getattr(request, 'limited', False):
            headers = _update_rate_limit(cache_key, limit=rate_limit, window=window_seconds, increment=False)
            resp = _problem_detail_response(
                request,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                title='rate_limit_exceeded',
                detail='Limite de 30 requisições por minuto excedido para este tenant.',
                type_suffix='rate-limit',
                extra={'rateLimit': {'limit': rate_limit, 'windowSeconds': window_seconds}},
            )
            resp['Retry-After'] = headers['RateLimit-Reset']
            for k, v in headers.items():
                resp[k] = v
            return resp

        # Valida cabeçalhos obrigatórios
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return _problem_detail_response(
                request,
                status_code=status.HTTP_400_BAD_REQUEST,
                title='idempotency_key_required',
                detail='Cabeçalho obrigatório.',
                type_suffix='idempotency-key',
                extra={'invalidParams': [{'name': 'Idempotency-Key', 'reason': 'Envie um UUID único por requisição.'}]},
            )

        tenant_header_problem = _validate_required_tenant_header(request, tenant_uuid)
        if tenant_header_problem is not None:
            return tenant_header_problem

        # Payload + idempotência
        try:
            tenant = get_object_or_404(Tenant, id=tenant_id)
        except Http404:
            return _problem_detail_response(
                request,
                status_code=status.HTTP_404_NOT_FOUND,
                title='tenant_not_found',
                detail='Tenant não encontrado.',
                type_suffix='tenant',
            )

        request_serializer = FeatureScaffoldRequestSerializer(data=request.data)
        try:
            request_serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            return _validation_problem_response(request, exc)
        payload = request_serializer.validated_data

        scope = ScaffoldIdempotencyScope(tenant_id=tenant_uuid, feature_slug=payload['featureSlug'])
        registry = ScaffoldIdempotencyRegistry()
        if registry.should_block(scope, idempotency_key):
            return _problem_detail_response(
                request,
                status_code=status.HTTP_409_CONFLICT,
                title='idempotency_conflict',
                detail='Outro Idempotency-Key já foi utilizado para esta feature nas últimas 24 horas.',
                type_suffix='idempotency-replay',
                extra={'idempotencyKey': idempotency_key},
            )

        registrar = ScaffoldRegistrar(tenant=tenant)
        registration, created = registrar.register(payload, idempotency_key)
        registry.remember(scope, idempotency_key)

        # Serialização + ETag + Location
        serialized_payload = FeatureTemplateRegistrationSerializer(instance=registration).data
        etag_value = _compute_etag_for_payload(serialized_payload)
        location = f'/api/v1/tenants/{tenant_uuid}/features/scaffold/{registration.feature_slug}'

        if not created:
            precond = _precondition_response_if_needed(
                request,
                idempotency_key=idempotency_key,
                etag_value=etag_value,
                location=location,
            )
            if precond is not None:
                return precond

        resp = Response(serialized_payload, status=status.HTTP_201_CREATED)
        resp['Idempotency-Key'] = idempotency_key
        resp['ETag'] = etag_value
        resp['Location'] = location
        if not created:
            resp.status_code = status.HTTP_200_OK

        # Rate limit headers pós-sucesso
        rate_headers = _update_rate_limit(cache_key, limit=rate_limit, window=window_seconds, increment=True)
        for k, v in rate_headers.items():
            resp[k] = v
        return resp


class DesignSystemStoryViewSet(ViewSet):
    http_method_names = ['get']

    def list(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        pagination = _parse_pagination(request)
        if isinstance(pagination, Response):
            return pagination
        page, page_size = pagination

        parsed = _parse_optional_tenant_header(request, request.headers.get('X-Tenant-Id'))
        if isinstance(parsed, Response):
            return parsed
        tenant_filter = parsed

        queryset = DesignSystemStory.objects.select_related('tenant').order_by('-updated_at')
        queryset = _apply_story_filters(
            queryset,
            tenant_filter,
            request.query_params.get('componentId'),
            request.query_params.get('tag'),
        )

        serialized, current_page, total_pages, total_items = _paginate_and_serialize(
            queryset, page, page_size
        )

        payload = {
            'data': serialized,
            'pagination': {
                'page': current_page,
                'perPage': page_size,
                'totalItems': total_items,
                'totalPages': total_pages,
            },
        }
        etag_value = _compute_etag_for_payload(payload)
        not_modified = _respond_not_modified_if_needed(request, etag_value)
        if not_modified is not None:
            return not_modified

        response = Response(payload, status=status.HTTP_200_OK)
        response['ETag'] = etag_value
        return response


@method_decorator(
    ratelimit(
        key='header:x-tenant-id',
        rate='60/m',
        method='GET',
        block=False,
    ),
    name='get',
)
class TenantThemeView(APIView):
    def get(self, request: HttpRequest, tenant_id: UUID, *args: Any, **kwargs: Any) -> Response:
        rate_limit = 60
        window_seconds = 60
        tenant_uuid = str(tenant_id)
        cache_key = f'foundation:tenant-theme:ratelimit:{tenant_uuid}'

        tenant_header_problem = _validate_required_tenant_header(request, tenant_uuid)
        if tenant_header_problem is not None:
            return tenant_header_problem

        if getattr(request, 'limited', False):
            headers = _update_rate_limit(cache_key, limit=rate_limit, window=window_seconds, increment=False)
            resp = _problem_detail_response(
                request,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                title='rate_limit_exceeded',
                detail='Limite de 60 requisições por minuto excedido.',
                type_suffix='rate-limit',
                extra={'rateLimit': {'limit': rate_limit, 'windowSeconds': window_seconds}},
            )
            resp['Retry-After'] = headers['RateLimit-Reset']
            for k, v in headers.items():
                resp[k] = v
            return resp

        try:
            tenant = get_object_or_404(Tenant, id=tenant_id)
        except Http404:
            resp = _problem_detail_response(
                request,
                status_code=status.HTTP_404_NOT_FOUND,
                title='tenant_not_found',
                detail='Tenant não encontrado.',
                type_suffix='tenant',
            )
            rate_headers = _update_rate_limit(cache_key, limit=rate_limit, window=window_seconds, increment=False)
            for k, v in rate_headers.items():
                resp[k] = v
            return resp

        with use_tenant(tenant.id):
            scoped = TenantThemeToken.objects.scoped(tenant.id)
            default_token = (
                scoped.filter(is_default=True).order_by('-updated_at').first()
                or scoped.order_by('-updated_at').first()
            )

            if default_token is None:
                resp = _problem_detail_response(
                    request,
                    status_code=status.HTTP_404_NOT_FOUND,
                    title='tenant_theme_not_found',
                    detail='Tema não encontrado para este tenant.',
                    type_suffix='tenant-theme',
                )
                rate_headers = _update_rate_limit(cache_key, limit=rate_limit, window=window_seconds, increment=False)
                for k, v in rate_headers.items():
                    resp[k] = v
                return resp

            tokens = list(scoped.filter(version=default_token.version))

        serializer = TenantThemeSerializer(instance={'tenant': tenant, 'tokens': tokens})
        payload = serializer.data

        etag_value = _compute_etag_for_payload(payload)
        not_modified = _respond_not_modified_if_needed(request, etag_value)
        if not_modified is not None:
            rate_headers = _update_rate_limit(cache_key, limit=rate_limit, window=window_seconds, increment=False)
            for k, v in rate_headers.items():
                not_modified[k] = v
            return not_modified

        response = Response(payload, status=status.HTTP_200_OK)
        response['ETag'] = etag_value

        rate_headers = _update_rate_limit(cache_key, limit=rate_limit, window=window_seconds, increment=True)
        for k, v in rate_headers.items():
            response[k] = v

        return response


@method_decorator(
    ratelimit(
        key='header:x-tenant-id',
        rate='60/m',
        method='GET',
        block=False,
    ),
    name='get',
)
class TenantSuccessMetricListView(APIView):
    def get(self, request: HttpRequest, tenant_id: UUID, *args: Any, **kwargs: Any) -> Response:
        rate_limit = 60
        window_seconds = 60
        tenant_uuid = str(tenant_id)
        cache_key = f'foundation:tenant-metrics:ratelimit:{tenant_uuid}'

        tenant_header_problem = _validate_required_tenant_header(request, tenant_uuid)
        if tenant_header_problem is not None:
            return tenant_header_problem

        if getattr(request, 'limited', False):
            headers = _update_rate_limit(cache_key, limit=rate_limit, window=window_seconds, increment=False)
            resp = _problem_detail_response(
                request,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                title='rate_limit_exceeded',
                detail='Limite de 60 requisições por minuto excedido.',
                type_suffix='rate-limit',
                extra={'rateLimit': {'limit': rate_limit, 'windowSeconds': window_seconds}},
            )
            resp['Retry-After'] = headers['RateLimit-Reset']
            for k, v in headers.items():
                resp[k] = v
            return resp

        pagination = _parse_pagination(request)
        if isinstance(pagination, Response):
            return pagination
        page, page_size = pagination

        queryset = FeatureTemplateMetric.objects.filter(tenant_id=tenant_uuid).order_by('-collected_at')
        paginator = Paginator(queryset, page_size)
        if paginator.count == 0:
            serialized: list[dict[str, Any]] = []
            current_page, total_pages = page, 0
            total_items = 0
        else:
            try:
                page_obj = paginator.page(page)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            serialized = SuccessMetricSerializer(page_obj.object_list, many=True).data
            current_page, total_pages, total_items = page_obj.number, paginator.num_pages, paginator.count

        payload = {
            'data': serialized,
            'pagination': {
                'page': current_page,
                'perPage': page_size,
                'totalItems': total_items,
                'totalPages': total_pages,
            },
        }
        response = Response(payload, status=status.HTTP_200_OK)
        rate_headers = _update_rate_limit(cache_key, limit=rate_limit, window=window_seconds, increment=True)
        for k, v in rate_headers.items():
            response[k] = v

        return response
