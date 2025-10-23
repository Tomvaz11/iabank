from __future__ import annotations

from typing import Any
from uuid import UUID

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.foundation.serializers import (
    FeatureScaffoldRequestSerializer,
    FeatureTemplateRegistrationSerializer,
)
from backend.apps.foundation.services.scaffold_registrar import ScaffoldRegistrar
from backend.apps.tenancy.models.tenant import Tenant


class RegisterFeatureScaffoldView(APIView):
    def post(self, request: HttpRequest, tenant_id: UUID, *args: Any, **kwargs: Any) -> Response:
        tenant_uuid = str(tenant_id)
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

        registrar = ScaffoldRegistrar(tenant=tenant)
        registration, created = registrar.register(request_serializer.validated_data, idempotency_key)

        response_serializer = FeatureTemplateRegistrationSerializer(instance=registration)
        response = Response(response_serializer.data, status=status.HTTP_201_CREATED)
        response['Idempotency-Key'] = idempotency_key
        response['Location'] = f'/api/v1/tenants/{tenant_uuid}/features/scaffold/{registration.feature_slug}'

        if not created:
            response.status_code = status.HTTP_200_OK

        return response
