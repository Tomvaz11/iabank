from __future__ import annotations

from typing import Any, Dict, Optional

import structlog
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .managers import use_tenant
from .models import Tenant, TenantThemeToken
from .services.seed_idempotency import SeedIdempotencyService
from .services.seed_manifest_validator import (
    RateLimitDecision,
    SeedManifestValidator,
    SimpleRateLimiter,
    ValidationResult,
)

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


class SeedProfileValidateView(APIView):
    validator = SeedManifestValidator()
    rate_limiter = SimpleRateLimiter()

    def post(self, request: HttpRequest) -> Response:
        manifest = self._extract_manifest(request)
        tenant_slug, environment, idempotency_key, missing = self._parse_headers(request)
        if missing:
            return self._problem_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                title='missing_headers',
                detail=f'Cabeçalhos obrigatórios ausentes: {", ".join(missing)}.',
                manifest=manifest,
            )

        tenant = Tenant.objects.filter(slug=tenant_slug).first()
        if tenant is None:
            return self._problem_response(
                status_code=status.HTTP_404_NOT_FOUND,
                title='tenant_not_found',
                detail='Tenant não encontrado para validação do manifesto.',
                manifest=manifest,
            )

        validation = self.validator.validate_manifest(manifest, environment=environment)
        idempo_service = SeedIdempotencyService(tenant.id)
        mode = manifest.get('mode', 'baseline') if isinstance(manifest, dict) else 'baseline'
        idempo_decision = idempo_service.ensure_entry(
            environment=str(environment),
            idempotency_key=str(idempotency_key),
            manifest_hash=validation.manifest_hash,
            mode=str(mode),
        )

        if idempo_decision.outcome == 'conflict':
            response = self._problem_response(
                status_code=status.HTTP_409_CONFLICT,
                title='idempotency_conflict',
                detail='Já existe resposta para esta Idempotency-Key com manifesto diferente.',
                manifest=manifest,
            )
            self._apply_rate_limit_headers(response, manifest)
            return response

        if idempo_decision.cached_response is not None:
            return idempo_decision.cached_response

        rate_limit_decision = self._enforce_rate_limit(
            tenant_id=tenant.id,
            environment=str(environment),
            manifest=manifest,
        )
        if not rate_limit_decision.allowed:
            response = self._rate_limit_response(manifest)
            return self._cache_and_respond(
                response=response,
                manifest=manifest,
                rate_limit_decision=rate_limit_decision,
                idempo_service=idempo_service,
                environment=str(environment),
                idempotency_key=str(idempotency_key),
                manifest_hash=validation.manifest_hash,
            )

        if not validation.valid:
            response = self._validation_error_response(validation)
            return self._cache_and_respond(
                response=response,
                manifest=manifest,
                rate_limit_decision=rate_limit_decision,
                idempo_service=idempo_service,
                environment=str(environment),
                idempotency_key=str(idempotency_key),
                manifest_hash=validation.manifest_hash,
            )

        response = self._success_response(manifest, validation)
        return self._cache_and_respond(
            response=response,
            manifest=manifest,
            rate_limit_decision=rate_limit_decision,
            idempo_service=idempo_service,
            environment=str(environment),
            idempotency_key=str(idempotency_key),
            manifest_hash=validation.manifest_hash,
        )

    def _problem_response(
        self,
        *,
        status_code: int,
        title: str,
        detail: str,
        manifest: Dict[str, Any] | None,
    ) -> Response:
        problem = {
            'type': 'https://iabank.local/problems/seed/validate-manifest',
            'title': title,
            'status': status_code,
            'detail': detail,
            'instance': '/api/v1/seed-profiles/validate',
        }
        if manifest is not None:
            problem['received_manifest'] = bool(manifest)
        return Response(problem, status=status_code)

    def _apply_rate_limit_headers(
        self,
        response: Response,
        manifest: Dict[str, Any] | None,
        decision: Optional[RateLimitDecision] = None,
    ) -> None:
        limit, window_seconds = self.validator.extract_rate_limit(manifest)
        remaining = decision.remaining if decision else limit
        retry_after = decision.retry_after if decision else window_seconds

        response['RateLimit-Limit'] = str(limit)
        response['RateLimit-Remaining'] = str(max(0, remaining))
        response['RateLimit-Reset'] = str(max(1, retry_after))
        response['Retry-After'] = str(max(1, retry_after))

    def _enforce_rate_limit(
        self,
        *,
        tenant_id: Any,
        environment: str,
        manifest: Dict[str, Any] | None,
    ) -> RateLimitDecision:
        limit, window_seconds = self.validator.extract_rate_limit(manifest)
        return self.rate_limiter.check(
            tenant_id=tenant_id,
            environment=environment,
            limit=limit,
            window_seconds=window_seconds,
        )

    @staticmethod
    def _extract_manifest(request: HttpRequest) -> Dict[str, Any] | None:
        return request.data.get('manifest') if isinstance(request.data, dict) else None

    @staticmethod
    def _parse_headers(request: HttpRequest) -> tuple[Optional[str], Optional[str], Optional[str], list[str]]:
        tenant_slug = request.headers.get('X-Tenant-ID')
        environment = request.headers.get('X-Environment')
        idempotency_key = request.headers.get('Idempotency-Key')
        missing = [name for name, value in [('X-Tenant-ID', tenant_slug), ('X-Environment', environment), ('Idempotency-Key', idempotency_key)] if not value]
        return tenant_slug, environment, idempotency_key, missing

    def _rate_limit_response(self, manifest: Dict[str, Any] | None) -> Response:
        return self._problem_response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            title='rate_limit_exceeded',
            detail='Validação sujeita a RateLimit-*; tente novamente após o Retry-After informado.',
            manifest=manifest,
        )

    def _validation_error_response(self, validation: ValidationResult) -> Response:
        return Response(
            {
                'type': 'https://iabank.local/problems/seed/manifest-invalid',
                'title': 'manifest_invalid',
                'status': status.HTTP_422_UNPROCESSABLE_ENTITY,
                'detail': 'Manifesto v1 inválido ou fora do contrato esperado.',
                'violations': validation.violations,
                'issues': validation.issues,
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    def _success_response(self, manifest: Dict[str, Any] | None, validation: ValidationResult) -> Response:
        body = {
            'valid': True,
            'issues': [],
            'normalized_version': validation.normalized_version,
            'caps': self.validator.extract_caps(manifest),
            'manifest_hash': validation.manifest_hash,
        }
        return Response(body, status=status.HTTP_200_OK)

    def _cache_and_respond(
        self,
        *,
        response: Response,
        manifest: Dict[str, Any] | None,
        rate_limit_decision: RateLimitDecision,
        idempo_service: SeedIdempotencyService,
        environment: str,
        idempotency_key: str,
        manifest_hash: str,
    ) -> Response:
        self._apply_rate_limit_headers(response, manifest, rate_limit_decision)
        idempo_service.cache_response(
            environment=environment,
            idempotency_key=idempotency_key,
            manifest_hash=manifest_hash,
            response=response,
        )
        return response
