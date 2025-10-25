from __future__ import annotations

import hashlib
import json
import time
from typing import Any
from uuid import UUID

from django.core.cache import cache
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.foundation.idempotency import (
    ScaffoldIdempotencyRegistry,
    ScaffoldIdempotencyScope,
)
from backend.apps.foundation.serializers import (
    FeatureScaffoldRequestSerializer,
    FeatureTemplateRegistrationSerializer,
    TenantThemeSerializer,
)
from backend.apps.foundation.services.scaffold_registrar import ScaffoldRegistrar
from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import Tenant, TenantThemeToken
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

        if getattr(request, 'limited', False):
            headers = _update_rate_limit(
                cache_key,
                limit=rate_limit,
                window=window_seconds,
                increment=False,
            )
            response = Response(
                {
                    'errors': {
                        'rateLimit': [
                            'Limite de 30 requisições por minuto excedido para este tenant.'
                        ]
                    }
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
            response['Retry-After'] = headers['RateLimit-Reset']
            for key, value in headers.items():
                response[key] = value
            return response

        idempotency_key = request.headers.get('Idempotency-Key')

        if not idempotency_key:
            return Response(
                {'errors': {'Idempotency-Key': ['Cabeçalho obrigatório.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tenant_header = request.headers.get('X-Tenant-Id')
        if tenant_header != tenant_uuid:
            return Response(
                {'errors': {'X-Tenant-Id': ['Cabeçalho X-Tenant-Id inválido ou ausente.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tenant = get_object_or_404(Tenant, id=tenant_id)

        request_serializer = FeatureScaffoldRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        payload = request_serializer.validated_data
        scope = ScaffoldIdempotencyScope(
            tenant_id=tenant_uuid,
            feature_slug=payload['featureSlug'],
        )
        registry = ScaffoldIdempotencyRegistry()

        if registry.should_block(scope, idempotency_key):
            return Response(
                {
                    'errors': {
                        'Idempotency-Key': [
                            'Outro Idempotency-Key já foi utilizado para esta feature nas últimas 24 horas.'
                        ]
                    }
                },
                status=status.HTTP_409_CONFLICT,
            )

        registrar = ScaffoldRegistrar(tenant=tenant)
        registration, created = registrar.register(payload, idempotency_key)

        registry.remember(scope, idempotency_key)

        response_serializer = FeatureTemplateRegistrationSerializer(instance=registration)
        serialized_payload = response_serializer.data
        etag_source = json.dumps(serialized_payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        etag_hash = hashlib.sha256(etag_source).hexdigest()
        etag_value = f'"{etag_hash}"'

        location = f'/api/v1/tenants/{tenant_uuid}/features/scaffold/{registration.feature_slug}'

        if not created:
            raw_if_none_match = request.headers.get('If-None-Match')
            if raw_if_none_match:
                requested_etags = {token.strip() for token in raw_if_none_match.split(',') if token.strip()}
                if '*' in requested_etags:
                    precondition = Response(
                        {
                            'errors': {
                                'If-None-Match': [
                                    'Registro de scaffolding já existe para esta feature.'
                                ]
                            }
                        },
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

        response = Response(serialized_payload, status=status.HTTP_201_CREATED)
        response['Idempotency-Key'] = idempotency_key
        response['ETag'] = etag_value
        response['Location'] = location

        if not created:
            response.status_code = status.HTTP_200_OK

        if response.status_code == status.HTTP_200_OK:
            response['ETag'] = etag_value

        rate_headers = _update_rate_limit(
            cache_key,
            limit=rate_limit,
            window=window_seconds,
            increment=True,
        )
        for key, value in rate_headers.items():
            response[key] = value

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

        tenant_header = request.headers.get('X-Tenant-Id')
        if tenant_header != tenant_uuid:
            return Response(
                {'errors': {'X-Tenant-Id': ['Cabeçalho X-Tenant-Id inválido ou ausente.']}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if getattr(request, 'limited', False):
            headers = _update_rate_limit(
                cache_key,
                limit=rate_limit,
                window=window_seconds,
                increment=False,
            )
            response = Response(
                {'errors': {'rateLimit': ['Limite de 60 requisições por minuto excedido.']}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
            response['Retry-After'] = headers['RateLimit-Reset']
            for key, value in headers.items():
                response[key] = value
            return response

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

        etag_source = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
        etag_value = f'"{hashlib.sha256(etag_source).hexdigest()}"'

        if_none_match = request.headers.get('If-None-Match')
        if if_none_match:
            requested_etags = {token.strip() for token in if_none_match.split(',') if token.strip()}
            if '*' in requested_etags or etag_value in requested_etags:
                not_modified = Response(status=status.HTTP_304_NOT_MODIFIED)
                not_modified['ETag'] = etag_value
                rate_headers = _update_rate_limit(
                    cache_key,
                    limit=rate_limit,
                    window=window_seconds,
                    increment=False,
                )
                for key, value in rate_headers.items():
                    not_modified[key] = value
                return not_modified

        response = Response(payload, status=status.HTTP_200_OK)
        response['ETag'] = etag_value

        rate_headers = _update_rate_limit(
            cache_key,
            limit=rate_limit,
            window=window_seconds,
            increment=True,
        )
        for key, value in rate_headers.items():
            response[key] = value

        return response
