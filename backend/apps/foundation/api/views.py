from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
import time
from django.core.cache import cache
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
)
from backend.apps.foundation.services.scaffold_registrar import ScaffoldRegistrar
from backend.apps.tenancy.models.tenant import Tenant
from ratelimit.decorators import ratelimit


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
        # Rate limit policy (aligned to ADR-011): 30 req/min per tenant
        RATE_LIMIT = 30
        WINDOW_SECONDS = 60

        def rate_key(tid: str) -> str:
            return f'foundation:scaffold:ratelimit:{tid}'

        def update_and_get_rate_headers(tid: str, limited: bool = False) -> dict[str, str]:
            now = int(time.time())
            key = rate_key(tid)
            data = cache.get(key)
            if not isinstance(data, dict) or 'count' not in data or 'window_start' not in data:
                data = {'count': 0, 'window_start': now}

            # reset window if expired
            elapsed = now - int(data['window_start'])
            if elapsed >= WINDOW_SECONDS:
                data = {'count': 0, 'window_start': now}
                elapsed = 0

            # only increment if request is not already blocked by decorator
            if not limited:
                data['count'] = int(data['count']) + 1

            # remaining and reset computation
            remaining = max(0, RATE_LIMIT - int(data['count']))
            reset = max(1, WINDOW_SECONDS - elapsed)

            # persist with TTL until window end
            cache.set(key, data, timeout=reset)

            headers = {
                'RateLimit-Limit': f'{RATE_LIMIT};w={WINDOW_SECONDS}',
                'RateLimit-Remaining': str(remaining),
                'RateLimit-Reset': str(reset),
            }
            return headers

        tenant_uuid = str(tenant_id)

        if getattr(request, 'limited', False):
            headers = update_and_get_rate_headers(tenant_uuid, limited=True)
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
            # Required headers per ADR-011 / Runbook
            response['Retry-After'] = headers['RateLimit-Reset']
            for k, v in headers.items():
                response[k] = v
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

        # Build success response
        response = Response(serialized_payload, status=status.HTTP_201_CREATED)
        response['Idempotency-Key'] = idempotency_key
        response['ETag'] = etag_value
        response['Location'] = location

        if not created:
            response.status_code = status.HTTP_200_OK

        if response.status_code == status.HTTP_200_OK:
            response['ETag'] = etag_value

        # Attach RateLimit headers on success as well
        rate_headers = update_and_get_rate_headers(tenant_uuid, limited=False)
        for k, v in rate_headers.items():
            response[k] = v

        return response
