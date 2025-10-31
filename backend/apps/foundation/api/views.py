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
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import status
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
def _parse_pagination(request: HttpRequest) -> tuple[int, int] | Response:
    try:
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 25))
    except ValueError:
        return Response(
            {'errors': {'pagination': ['Parâmetros de paginação inválidos.']}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if page < 1 or page_size < 1 or page_size > 100:
        return Response(
            {'errors': {'pagination': ['Parâmetros de paginação fora do intervalo permitido.']}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return page, page_size


def _parse_optional_tenant_header(header_value: str | None) -> UUID | None | Response:
    if not header_value:
        return None
    try:
        return uuid.UUID(header_value)
    except ValueError:
        return Response(
            {'errors': {'X-Tenant-Id': ['Cabeçalho X-Tenant-Id inválido.']}},
            status=status.HTTP_400_BAD_REQUEST,
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
        precondition = Response(
            {'errors': {'If-None-Match': ['Registro de scaffolding já existe para esta feature.']}},
            status=status.HTTP_412_PRECONDITION_FAILED,
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
            resp = Response(
                {'errors': {'rateLimit': ['Limite de 30 requisições por minuto excedido para este tenant.']}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
            resp['Retry-After'] = headers['RateLimit-Reset']
            for k, v in headers.items():
                resp[k] = v
            return resp

        # Valida cabeçalhos obrigatórios
        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response({'errors': {'Idempotency-Key': ['Cabeçalho obrigatório.']}}, status=status.HTTP_400_BAD_REQUEST)

        if request.headers.get('X-Tenant-Id') != tenant_uuid:
            return Response(
                {'errors': {'X-Tenant-Id': ['Cabeçalho X-Tenant-Id inválido ou ausente.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Payload + idempotência
        tenant = get_object_or_404(Tenant, id=tenant_id)
        request_serializer = FeatureScaffoldRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        payload = request_serializer.validated_data

        scope = ScaffoldIdempotencyScope(tenant_id=tenant_uuid, feature_slug=payload['featureSlug'])
        registry = ScaffoldIdempotencyRegistry()
        if registry.should_block(scope, idempotency_key):
            return Response(
                {'errors': {'Idempotency-Key': ['Outro Idempotency-Key já foi utilizado para esta feature nas últimas 24 horas.']}},
                status=status.HTTP_409_CONFLICT,
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

        parsed = _parse_optional_tenant_header(request.headers.get('X-Tenant-Id'))
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

        if request.headers.get('X-Tenant-Id') != tenant_uuid:
            return Response(
                {'errors': {'X-Tenant-Id': ['Cabeçalho X-Tenant-Id inválido ou ausente.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if getattr(request, 'limited', False):
            headers = _update_rate_limit(cache_key, limit=rate_limit, window=window_seconds, increment=False)
            resp = Response({'errors': {'rateLimit': ['Limite de 60 requisições por minuto excedido.']}}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            resp['Retry-After'] = headers['RateLimit-Reset']
            for k, v in headers.items():
                resp[k] = v
            return resp

        tenant = get_object_or_404(Tenant, id=tenant_id)

        with use_tenant(tenant.id):
            scoped = TenantThemeToken.objects.scoped(tenant.id)
            default_token = (
                scoped.filter(is_default=True).order_by('-updated_at').first()
                or scoped.order_by('-updated_at').first()
            )

            if default_token is None:
                return Response(status=status.HTTP_404_NOT_FOUND)

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

        if request.headers.get('X-Tenant-Id') != tenant_uuid:
            return Response(
                {'errors': {'X-Tenant-Id': ['Cabeçalho X-Tenant-Id inválido ou ausente.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if getattr(request, 'limited', False):
            headers = _update_rate_limit(cache_key, limit=rate_limit, window=window_seconds, increment=False)
            resp = Response({'errors': {'rateLimit': ['Limite de 60 requisições por minuto excedido.']}}, status=status.HTTP_429_TOO_MANY_REQUESTS)
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
