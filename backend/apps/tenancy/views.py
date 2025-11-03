from __future__ import annotations

from typing import Any, Dict

import structlog
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .managers import use_tenant
from .models import Tenant, TenantThemeToken

logger = structlog.get_logger('backend.apps.tenancy')


def _mask_domain(domain: str) -> str:
    parts = domain.split('.')
    if not parts:
        return '***'
    parts[0] = '***'
    return '.'.join(parts)


def _require_tenant_header(request: HttpRequest, tenant_slug: str) -> str:
    header = request.headers.get('X-Tenant-Id')
    if not header:
        raise ValueError('missing-header')
    if header != tenant_slug:
        raise ValueError('mismatch')
    return header


class TenantThemeView(APIView):
    def get(self, request: HttpRequest, tenant_slug: str) -> Response:
        try:
            _require_tenant_header(request, tenant_slug)
        except ValueError as exc:  # pragma: no cover - mapped para respostas específicas
            if str(exc) == 'missing-header':
                return Response(
                    {'detail': 'Cabeçalho X-Tenant-Id é obrigatório.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_404_NOT_FOUND)

        tenant = get_object_or_404(Tenant, slug=tenant_slug)

        with use_tenant(tenant.id):
            token = (
                TenantThemeToken.objects.scoped(tenant.id).filter(is_default=True).first()
                or TenantThemeToken.objects.scoped(tenant.id).first()
            )

        if token is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        payload: Dict[str, Any] = {
            'tenantId': tenant.slug,
            'version': token.version,
            'category': token.category,
            'tokens': token.json_payload,
        }
        return Response(payload)


class TenantSuccessMetricsView(APIView):
    def get(self, request: HttpRequest, tenant_slug: str) -> Response:
        header = request.headers.get('X-Tenant-Id')
        tenant = get_object_or_404(Tenant, slug=tenant_slug)

        if header != tenant.slug:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        logger.info(
            'tenant_success_metrics',
            tenant=tenant.slug,
            masked_domain=_mask_domain(tenant.primary_domain),
        )

        with use_tenant(tenant.id):
            # Placeholder — integração real será implementada nas US subsequentes.
            data = {
                'results': [],
                'tenantId': tenant.slug,
            }

        return Response(data)
