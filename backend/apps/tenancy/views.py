from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Sequence
from uuid import UUID

import structlog
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.tenancy.serializers.seed_runs import SeedRunCreateSerializer, SeedRunSerializer
from .managers import use_tenant
from .models import SeedRBAC, SeedRun, Tenant, TenantThemeToken
from .services.seed_idempotency import IdempotencyDecision, SeedIdempotencyService
from .services.seed_manifest_validator import (
    RateLimitDecision,
    SeedManifestValidator,
    SimpleRateLimiter,
    ValidationResult,
)
from .services.seed_preflight import PreflightContext, SeedPreflightConfig, SeedPreflightService
from .services.seed_queue import QueueDecision, SeedQueueService
from .services.seed_queue_gc import SeedQueueGC
from .services.seed_runs import SeedRunService

logger = structlog.get_logger('backend.apps.tenancy')


@dataclass
class SeedRunCreateContext:
    request: HttpRequest
    tenant_slug: str
    environment: str
    idempotency_key: str
    subject: str
    tenant: Optional[Tenant] = None
    manifest: Optional[Dict[str, Any]] = None
    manifest_path: Optional[str] = None
    dry_run: bool = False
    mode: str = 'baseline'
    requested_by: str = ''
    roles: Sequence[str] = ()
    validation: Optional[ValidationResult] = None
    rate_decision: Optional[RateLimitDecision] = None
    idempo_service: Optional[SeedIdempotencyService] = None
    idempo_decision: Optional[IdempotencyDecision] = None
    queue_decision: Optional[QueueDecision] = None
    seed_run: Optional[SeedRun] = None


@dataclass
class SeedRunDetailContext:
    request: HttpRequest
    seed_run_id: UUID
    tenant_slug: str
    environment: str
    idempotency_key: Optional[str]
    subject: str
    tenant: Optional[Tenant] = None
    seed_run: Optional[SeedRun] = None
    roles: Sequence[str] = ()
    rate_decision: Optional[RateLimitDecision] = None


@dataclass
class SeedRunCancelContext:
    request: HttpRequest
    seed_run_id: UUID
    tenant_slug: str
    environment: str
    idempotency_key: str
    subject: str
    tenant: Optional[Tenant] = None
    seed_run: Optional[SeedRun] = None
    roles: Sequence[str] = ()
    rate_decision: Optional[RateLimitDecision] = None
    idempo_service: Optional[SeedIdempotencyService] = None
    idempo_decision: Optional[IdempotencyDecision] = None


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

        config = SeedPreflightConfig.from_env()
        if environment not in config.allowed_environments:
            return self._problem_response(
                status_code=status.HTTP_403_FORBIDDEN,
                title='environment_not_allowed',
                detail=f"Environment '{environment}' nao autorizado para validação de seed profiles.",
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


class SeedRunViewBase(APIView):
    validator = SeedManifestValidator()
    rate_limiter = SimpleRateLimiter()
    queue_service = SeedQueueService()
    queue_gc = SeedQueueGC()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.run_service = SeedRunService(queue_service=self.queue_service)
        self.preflight_service = SeedPreflightService()

    def _parse_headers(
        self,
        request: HttpRequest,
        *,
        require_idempotency: bool = True,
    ) -> tuple[Optional[str], Optional[str], Optional[str], str, list[str]]:
        tenant_slug = request.headers.get('X-Tenant-ID')
        environment = request.headers.get('X-Environment')
        idempotency_key = request.headers.get('Idempotency-Key')
        subject = request.headers.get('X-Seed-Subject', 'api:seed-runs')

        required: list[tuple[str, Optional[str]]] = [('X-Tenant-ID', tenant_slug), ('X-Environment', environment)]
        if require_idempotency:
            required.append(('Idempotency-Key', idempotency_key))

        missing = [name for name, value in required if not value]
        return tenant_slug, environment, idempotency_key, subject, missing

    def _problem_response(
        self,
        *,
        status_code: int,
        title: str,
        detail: str,
        instance: str,
    ) -> Response:
        return Response(
            {
                'type': f'https://iabank.local/problems/seed/{title}',
                'title': title,
                'status': status_code,
                'detail': detail,
                'instance': instance,
            },
            status=status_code,
        )

    def _apply_rate_limit_headers(self, response: Response, decision: RateLimitDecision) -> None:
        reset_seconds = max(1, int((decision.reset_at - timezone.now()).total_seconds()))
        response['RateLimit-Limit'] = str(decision.limit)
        response['RateLimit-Remaining'] = str(max(0, decision.remaining))
        response['RateLimit-Reset'] = str(reset_seconds)
        response['Retry-After'] = str(max(1, decision.retry_after))

    def _enforce_rate_limit(self, *, tenant_id: UUID, environment: str, manifest: Dict[str, Any] | None) -> RateLimitDecision:
        limit, window_seconds = self.validator.extract_rate_limit(manifest)
        return self.rate_limiter.check(
            tenant_id=tenant_id,
            environment=environment,
            limit=limit,
            window_seconds=window_seconds,
        )

    def _rate_limit_response(self, manifest: Dict[str, Any] | None, decision: RateLimitDecision) -> Response:
        response = self._problem_response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            title='rate_limit_exceeded',
            detail='Requisição sujeita a RateLimit-*; tente novamente após o Retry-After informado.',
            instance='/api/v1/seed-runs',
        )
        self._apply_rate_limit_headers(response, decision)
        return response

    def _ensure_rbac(
        self,
        *,
        tenant_id: UUID,
        environment: str,
        subject: str,
        allowed_roles: Sequence[str],
    ) -> tuple[bool, list[str]]:
        with use_tenant(tenant_id):
            roles = list(
                SeedRBAC.objects.filter(environment=environment, subject=subject).values_list('role', flat=True)
            )
        allowed = any(role in allowed_roles for role in roles)
        return allowed, [str(role) for role in roles]

    def _compute_etag(self, seed_run: SeedRun) -> str:
        updated_at = seed_run.updated_at or timezone.now()
        payload = f'{seed_run.id}:{seed_run.status}:{seed_run.manifest_hash_sha256}:{updated_at.isoformat()}'
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def _serialize_seed_run(self, seed_run: SeedRun) -> dict[str, Any]:
        serializer = SeedRunSerializer(seed_run)
        return serializer.data

    def _tenant_or_response(self, tenant_slug: Optional[str], *, instance: str) -> tuple[Optional[Tenant], Optional[Response]]:
        tenant = Tenant.objects.filter(slug=tenant_slug).first()
        if tenant is None:
            return None, self._problem_response(
                status_code=status.HTTP_404_NOT_FOUND,
                title='tenant_not_found',
                detail='Tenant não encontrado.',
                instance=instance,
            )
        return tenant, None

    def _serializer_validated_data(
        self,
        *,
        request: HttpRequest,
        tenant_id: UUID,
        environment: str,
    ) -> tuple[Optional[dict[str, Any]], Optional[Response]]:
        serializer = SeedRunCreateSerializer(data=request.data)
        if serializer.is_valid():
            return serializer.validated_data, None

        response = Response(
            {
                'type': 'https://iabank.local/problems/seed/manifest-invalid',
                'title': 'manifest_invalid',
                'status': status.HTTP_422_UNPROCESSABLE_ENTITY,
                'detail': 'Payload deve conter manifest no formato esperado.',
                'violations': serializer.errors,
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
        rate_decision = self._enforce_rate_limit(
            tenant_id=tenant_id,
            environment=environment,
            manifest=request.data.get('manifest'),
        )
        self._apply_rate_limit_headers(response, rate_decision)
        return None, response

    def _preflight_or_response(
        self,
        *,
        tenant: Tenant,
        environment: str,
        manifest_path: str,
        requested_by: str,
        roles: Sequence[str],
        dry_run: bool,
    ) -> Optional[Response]:
        preflight = self.preflight_service.check(
            PreflightContext(
                tenant_id=str(tenant.id),
                environment=str(environment),
                manifest_path=manifest_path,
                requested_by=requested_by,
                roles=roles,
                dry_run=dry_run,
            )
        )
        if not preflight.allowed and preflight.problem:
            return Response(preflight.problem.as_dict(), status=preflight.problem.status)
        return None

    def _validation_or_response(
        self,
        *,
        manifest: Dict[str, Any],
        tenant_id: UUID,
        environment: str,
    ) -> tuple[Optional[ValidationResult], Optional[RateLimitDecision], Optional[Response]]:
        validation = self.validator.validate_manifest(manifest, environment=environment)
        rate_decision = self._enforce_rate_limit(
            tenant_id=tenant_id,
            environment=str(environment),
            manifest=manifest,
        )
        if validation.valid:
            return validation, rate_decision, None

        response = Response(
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
        self._apply_rate_limit_headers(response, rate_decision)
        return None, rate_decision, response

    def _preconditions_or_response(
        self,
        *,
        manifest: Dict[str, Any],
        tenant_id: UUID,
        environment: str,
        mode: str,
        rate_decision: RateLimitDecision,
    ) -> Optional[Response]:
        offpeak_problem = self.run_service.ensure_offpeak_window(
            manifest=manifest,
            environment=str(environment),
            mode=mode,
        )
        if offpeak_problem:
            response = Response(offpeak_problem.as_dict(), status=offpeak_problem.status)
            self._apply_rate_limit_headers(response, rate_decision)
            return response

        drift_problem = self.run_service.ensure_reference_drift(
            tenant_id=tenant_id,
            environment=str(environment),
            mode=mode,
            reference_datetime=self.run_service._parse_reference_datetime(manifest),
        )
        if drift_problem:
            response = Response(drift_problem.as_dict(), status=drift_problem.status)
            self._apply_rate_limit_headers(response, rate_decision)
            return response
        return None

    def _rate_limit_blocked(self, *, manifest: Dict[str, Any], rate_decision: RateLimitDecision) -> Optional[Response]:
        if rate_decision.allowed:
            return None
        return self._rate_limit_response(manifest, rate_decision)

    def _idempotency_create_decision(
        self,
        *,
        tenant: Tenant,
        environment: str,
        idempotency_key: str,
        manifest_hash: str,
        mode: str,
        rate_decision: RateLimitDecision,
    ) -> tuple[Optional[IdempotencyDecision], SeedIdempotencyService, Optional[Response]]:
        idempo_service = SeedIdempotencyService(tenant.id, context='seed_runs_api')
        idempo_service.cleanup_expired(environment=str(environment))
        decision = idempo_service.ensure_entry(
            environment=str(environment),
            idempotency_key=str(idempotency_key),
            manifest_hash=manifest_hash,
            mode=mode,
        )

        if decision.outcome == 'conflict':
            response = self._problem_response(
                status_code=status.HTTP_409_CONFLICT,
                title='idempotency_conflict',
                detail='Já existe resposta para esta Idempotency-Key com manifesto diferente.',
                instance='/api/v1/seed-runs',
            )
            self._apply_rate_limit_headers(response, rate_decision)
            return None, idempo_service, response

        if decision.cached_response is not None:
            return None, idempo_service, decision.cached_response

        if decision.outcome == 'replay' and decision.entry:
            with use_tenant(tenant.id):
                seed_run = (
                    SeedRun.objects.unscoped()
                    .select_related('seed_profile')
                    .filter(id=decision.entry.seed_run_id)
                    .first()
                )

            if seed_run:
                replay = self._response_for_seed_run(
                    seed_run=seed_run,
                    rate_limit=rate_decision,
                    idempotency_key=idempotency_key,
                    status_code=status.HTTP_201_CREATED,
                )
                idempo_service.cache_response(
                    environment=str(environment),
                    idempotency_key=str(idempotency_key),
                    manifest_hash=manifest_hash,
                    response=replay,
                    context='seed_runs_api',
                )
                return None, idempo_service, replay

            with use_tenant(tenant.id):
                decision.entry.delete()
            decision = idempo_service.ensure_entry(
                environment=str(environment),
                idempotency_key=str(idempotency_key),
                manifest_hash=manifest_hash,
                mode=mode,
            )

        return decision, idempo_service, None

    def _queue_request_or_response(
        self,
        *,
        tenant: Tenant,
        environment: str,
        mode: str,
        rate_decision: RateLimitDecision,
        idempo_decision: IdempotencyDecision,
    ) -> tuple[Optional[QueueDecision], Optional[Response]]:
        self.queue_gc.expire_stale(environment=str(environment))
        queue_ttl = SeedRunService.queue_ttl_for_mode(mode)
        decision, problem = self.run_service.request_slot(
            environment=str(environment),
            tenant_id=tenant.id,
            seed_run_id=None,
            now=timezone.now(),
            ttl=queue_ttl,
        )
        if not problem:
            return decision, None

        response = Response(problem.as_dict(), status=problem.status)
        self._apply_rate_limit_headers(response, rate_decision)
        if problem.retry_after is not None:
            response['Retry-After'] = str(problem.retry_after)
        if idempo_decision.outcome == 'new' and idempo_decision.entry:
            with use_tenant(tenant.id):
                idempo_decision.entry.delete()
        return None, response

    def _seed_run_or_response(
        self,
        *,
        tenant: Tenant,
        seed_run_id: UUID,
        instance: str,
    ) -> tuple[Optional[SeedRun], Optional[Response]]:
        with use_tenant(tenant.id):
            seed_run = (
                SeedRun.objects.unscoped()
                .select_related('seed_profile')
                .filter(id=seed_run_id, tenant=tenant)
                .first()
            )

        if seed_run is None:
            return None, self._problem_response(
                status_code=status.HTTP_404_NOT_FOUND,
                title='seed_run_not_found',
                detail='SeedRun não encontrado para o tenant informado.',
                instance=instance,
            )
        return seed_run, None

    def _environment_guard(
        self,
        *,
        seed_run: SeedRun,
        environment: str,
        instance: str,
    ) -> Optional[Response]:
        if str(seed_run.environment) != str(environment):
            return self._problem_response(
                status_code=status.HTTP_403_FORBIDDEN,
                title='environment_mismatch',
                detail='O ambiente informado não corresponde ao SeedRun solicitado.',
                instance=instance,
            )
        return None

    @staticmethod
    def _run_steps(ctx: Any, steps: Sequence[Callable[[Any], Optional[Response]]]) -> Optional[Response]:
        for step in steps:
            response = step(ctx)
            if response:
                return response
        return None

    def _response_for_seed_run(
        self,
        *,
        seed_run: SeedRun,
        rate_limit: RateLimitDecision,
        idempotency_key: Optional[str],
        status_code: int,
    ) -> Response:
        etag = self._compute_etag(seed_run)
        body = self._serialize_seed_run(seed_run)
        body['seed_run_id'] = str(seed_run.id)
        response = Response(body, status=status_code)
        self._apply_common_headers(
            response,
            etag=etag,
            rate_limit=rate_limit,
            idempotency_key=idempotency_key,
            seed_run_id=seed_run.id,
        )
        return response

    def _manifest_path(self, manifest_path: Optional[str], tenant_slug: str, environment: str) -> str:
        if manifest_path:
            return manifest_path
        return f'configs/seed_profiles/{environment}/{tenant_slug}.yaml'

    def _apply_common_headers(
        self,
        response: Response,
        *,
        etag: str,
        rate_limit: RateLimitDecision,
        idempotency_key: Optional[str],
        seed_run_id: Optional[UUID] = None,
    ) -> None:
        response['ETag'] = etag
        self._apply_rate_limit_headers(response, rate_limit)
        if idempotency_key:
            response['Idempotency-Key'] = idempotency_key
        if seed_run_id:
            response['Location'] = f'/api/v1/seed-runs/{seed_run_id}'

    def _manifest_tenant_mismatch(
        self,
        *,
        manifest: Dict[str, Any],
        tenant_slug: str,
        instance: str,
    ) -> Optional[Response]:
        metadata = manifest.get('metadata', {}) if isinstance(manifest, dict) else {}
        manifest_tenant = metadata.get('tenant')
        if manifest_tenant and manifest_tenant != tenant_slug:
            return self._problem_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                title='manifest_tenant_mismatch',
                detail='Manifesto pertence a outro tenant; revise o caminho informado.',
                instance=instance,
        )
        return None

    def _environment_mismatch(
        self,
        *,
        manifest: Dict[str, Any],
        environment: str,
        instance: str,
    ) -> Optional[Response]:
        metadata = manifest.get('metadata', {}) if isinstance(manifest, dict) else {}
        manifest_env = metadata.get('environment')
        if manifest_env and manifest_env != environment:
            return self._problem_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                title='manifest_environment_mismatch',
                detail='Manifesto aponta para outro ambiente; ajuste X-Environment ou o manifesto.',
                instance=instance,
            )
        return None


class SeedRunsView(SeedRunViewBase):
    # pipeline steps
    def _step_load_tenant(self, ctx: SeedRunCreateContext) -> Optional[Response]:
        tenant, response = self._tenant_or_response(ctx.tenant_slug, instance='/api/v1/seed-runs')
        if response:
            return response
        ctx.tenant = tenant
        return None

    def _step_validate_serializer(self, ctx: SeedRunCreateContext) -> Optional[Response]:
        assert ctx.tenant
        data, response = self._serializer_validated_data(
            request=ctx.request,
            tenant_id=ctx.tenant.id,
            environment=ctx.environment,
        )
        if response:
            return response
        assert data is not None
        manifest: Dict[str, Any] = data['manifest']
        ctx.manifest = manifest
        ctx.manifest_path = self._manifest_path(data.get('manifest_path'), ctx.tenant.slug, str(ctx.environment))
        ctx.dry_run = bool(data.get('dry_run', False))
        ctx.mode = str(data.get('mode') or manifest.get('mode') or 'baseline')
        ctx.requested_by = str(data.get('requested_by') or ctx.subject)
        return None

    def _step_rbac_preflight(self, ctx: SeedRunCreateContext) -> Optional[Response]:
        assert ctx.tenant and ctx.manifest is not None
        allowed, roles = self._ensure_rbac(
            tenant_id=ctx.tenant.id,
            environment=str(ctx.environment),
            subject=ctx.subject,
            allowed_roles=['seed-runner', 'seed-admin'],
        )
        if not allowed:
            return self._problem_response(
                status_code=status.HTTP_403_FORBIDDEN,
                title='rbac_forbidden',
                detail='Subject não autorizado a criar seed runs neste ambiente.',
                instance='/api/v1/seed-runs',
            )
        ctx.roles = roles
        return self._preflight_or_response(
            tenant=ctx.tenant,
            environment=str(ctx.environment),
            manifest_path=ctx.manifest_path or '',
            requested_by=ctx.requested_by,
            roles=ctx.roles,
            dry_run=ctx.dry_run,
        )

    def _step_manifest_consistency(self, ctx: SeedRunCreateContext) -> Optional[Response]:
        assert ctx.tenant and ctx.manifest is not None
        mismatch = self._manifest_tenant_mismatch(
            manifest=ctx.manifest,
            tenant_slug=ctx.tenant.slug,
            instance='/api/v1/seed-runs',
        )
        if mismatch:
            return mismatch
        return self._environment_mismatch(
            manifest=ctx.manifest,
            environment=str(ctx.environment),
            instance='/api/v1/seed-runs',
        )

    def _step_validation_rate(self, ctx: SeedRunCreateContext) -> Optional[Response]:
        assert ctx.tenant and ctx.manifest is not None
        validation, rate_decision, response = self._validation_or_response(
            manifest=ctx.manifest,
            tenant_id=ctx.tenant.id,
            environment=str(ctx.environment),
        )
        if response:
            return response
        ctx.validation = validation
        ctx.rate_decision = rate_decision
        return None

    def _step_preconditions(self, ctx: SeedRunCreateContext) -> Optional[Response]:
        assert ctx.manifest is not None and ctx.rate_decision is not None and ctx.tenant
        return self._preconditions_or_response(
            manifest=ctx.manifest,
            tenant_id=ctx.tenant.id,
            environment=str(ctx.environment),
            mode=ctx.mode,
            rate_decision=ctx.rate_decision,
        )

    def _step_idempotency(self, ctx: SeedRunCreateContext) -> Optional[Response]:
        assert ctx.validation and ctx.rate_decision and ctx.tenant
        decision, service, response = self._idempotency_create_decision(
            tenant=ctx.tenant,
            environment=str(ctx.environment),
            idempotency_key=str(ctx.idempotency_key),
            manifest_hash=ctx.validation.manifest_hash,
            mode=ctx.mode,
            rate_decision=ctx.rate_decision,
        )
        ctx.idempo_decision = decision
        ctx.idempo_service = service
        return response

    def _step_rate_limit_block(self, ctx: SeedRunCreateContext) -> Optional[Response]:
        assert ctx.manifest is not None and ctx.rate_decision and ctx.idempo_service and ctx.validation
        blocked = self._rate_limit_blocked(manifest=ctx.manifest, rate_decision=ctx.rate_decision)
        if not blocked:
            return None
        ctx.idempo_service.cache_response(
            environment=str(ctx.environment),
            idempotency_key=str(ctx.idempotency_key),
            manifest_hash=ctx.validation.manifest_hash,
            response=blocked,
            context='seed_runs_api',
        )
        return blocked

    def _step_queue(self, ctx: SeedRunCreateContext) -> Optional[Response]:
        assert ctx.tenant and ctx.rate_decision and ctx.idempo_decision
        decision, response = self._queue_request_or_response(
            tenant=ctx.tenant,
            environment=str(ctx.environment),
            mode=ctx.mode,
            rate_decision=ctx.rate_decision,
            idempo_decision=ctx.idempo_decision,
        )
        ctx.queue_decision = decision
        return response

    def _step_create_seed_run(self, ctx: SeedRunCreateContext) -> Optional[Response]:
        assert ctx.tenant and ctx.manifest is not None and ctx.validation and ctx.idempo_service
        decision = ctx.queue_decision
        idempo_decision = ctx.idempo_decision
        assert decision is not None and idempo_decision is not None

        creation = self.run_service.create_seed_run(
            tenant_id=ctx.tenant.id,
            environment=str(ctx.environment),
            manifest=ctx.manifest,
            manifest_path=ctx.manifest_path or self._manifest_path(None, ctx.tenant.slug, ctx.environment),
            idempotency_key=str(ctx.idempotency_key),
            requested_by=ctx.requested_by,
            dry_run=ctx.dry_run,
            mode=ctx.mode,
        )

        if idempo_decision.entry:
            with use_tenant(ctx.tenant.id):
                idempo_decision.entry.seed_run = creation.seed_run
                idempo_decision.entry.save(update_fields=['seed_run', 'updated_at'])

        entry = decision.entry
        if entry:
            entry.seed_run = creation.seed_run
            entry.tenant = creation.seed_run.tenant
            entry.save(update_fields=['seed_run', 'tenant', 'updated_at'])

        etag = self._compute_etag(creation.seed_run)
        body = self._serialize_seed_run(creation.seed_run)
        body['seed_run_id'] = str(creation.seed_run.id)
        body['manifest_hash'] = ctx.validation.manifest_hash

        response = Response(body, status=status.HTTP_201_CREATED)
        self._apply_common_headers(
            response,
            etag=etag,
            rate_limit=ctx.rate_decision,
            idempotency_key=str(ctx.idempotency_key),
            seed_run_id=creation.seed_run.id,
        )
        ctx.idempo_service.cache_response(
            environment=str(ctx.environment),
            idempotency_key=str(ctx.idempotency_key),
            manifest_hash=ctx.validation.manifest_hash,
            response=response,
            context='seed_runs_api',
        )
        return response

    def post(self, request: HttpRequest) -> Response:
        tenant_slug, environment, idempotency_key, subject, missing = self._parse_headers(request)
        if missing:
            return self._problem_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                title='missing_headers',
                detail=f'Cabeçalhos obrigatórios ausentes: {", ".join(missing)}.',
                instance='/api/v1/seed-runs',
            )

        ctx = SeedRunCreateContext(
            request=request,
            tenant_slug=str(tenant_slug),
            environment=str(environment),
            idempotency_key=str(idempotency_key),
            subject=subject,
        )

        steps = [
            self._step_load_tenant,
            self._step_validate_serializer,
            self._step_rbac_preflight,
            self._step_manifest_consistency,
            self._step_validation_rate,
            self._step_preconditions,
            self._step_idempotency,
            self._step_rate_limit_block,
            self._step_queue,
            self._step_create_seed_run,
        ]
        response = self._run_steps(ctx, steps)
        assert response is not None
        return response


class SeedRunDetailView(SeedRunViewBase):
    def _step_load_tenant(self, ctx: SeedRunDetailContext) -> Optional[Response]:
        tenant, response = self._tenant_or_response(ctx.tenant_slug, instance=f'/api/v1/seed-runs/{ctx.seed_run_id}')
        if response:
            return response
        ctx.tenant = tenant
        return None

    def _step_load_seed_run(self, ctx: SeedRunDetailContext) -> Optional[Response]:
        assert ctx.tenant
        seed_run, response = self._seed_run_or_response(
            tenant=ctx.tenant,
            seed_run_id=ctx.seed_run_id,
            instance=f'/api/v1/seed-runs/{ctx.seed_run_id}',
        )
        if response:
            return response
        ctx.seed_run = seed_run
        return None

    def _step_environment_guard(self, ctx: SeedRunDetailContext) -> Optional[Response]:
        assert ctx.seed_run
        return self._environment_guard(
            seed_run=ctx.seed_run,
            environment=str(ctx.environment),
            instance=f'/api/v1/seed-runs/{ctx.seed_run_id}',
        )

    def _step_rbac(self, ctx: SeedRunDetailContext) -> Optional[Response]:
        assert ctx.tenant
        allowed, roles = self._ensure_rbac(
            tenant_id=ctx.tenant.id,
            environment=str(ctx.environment),
            subject=ctx.subject,
            allowed_roles=['seed-runner', 'seed-admin', 'seed-read'],
        )
        if not allowed:
            return self._problem_response(
                status_code=status.HTTP_403_FORBIDDEN,
                title='rbac_forbidden',
                detail='Subject não autorizado a consultar seed runs neste ambiente.',
                instance=f'/api/v1/seed-runs/{ctx.seed_run_id}',
            )
        ctx.roles = roles
        return None

    def _step_preflight(self, ctx: SeedRunDetailContext) -> Optional[Response]:
        assert ctx.tenant and ctx.seed_run
        return self._preflight_or_response(
            tenant=ctx.tenant,
            environment=str(ctx.environment),
            manifest_path=ctx.seed_run.manifest_path or self._manifest_path(None, ctx.tenant.slug, str(ctx.environment)),
            requested_by=ctx.subject,
            roles=ctx.roles,
            dry_run=bool(ctx.seed_run.dry_run),
        )

    def _step_rate_limit(self, ctx: SeedRunDetailContext) -> Optional[Response]:
        assert ctx.tenant and ctx.seed_run
        manifest_like = {'rate_limit': ctx.seed_run.seed_profile.rate_limit if ctx.seed_run.seed_profile else {}}
        ctx.rate_decision = self._enforce_rate_limit(
            tenant_id=ctx.tenant.id,
            environment=str(ctx.environment),
            manifest=manifest_like,
        )
        if not ctx.rate_decision.allowed:
            return self._rate_limit_response(manifest_like, ctx.rate_decision)
        return None

    def _step_if_none_match(self, ctx: SeedRunDetailContext) -> Optional[Response]:
        assert ctx.seed_run and ctx.rate_decision
        etag = self._compute_etag(ctx.seed_run)
        if_none_match = ctx.request.headers.get('If-None-Match')
        if if_none_match and if_none_match == etag:
            response = Response(status=status.HTTP_304_NOT_MODIFIED)
            self._apply_common_headers(
                response,
                etag=etag,
                rate_limit=ctx.rate_decision,
                idempotency_key=ctx.idempotency_key,
                seed_run_id=ctx.seed_run.id,
            )
            return response
        ctx.request.META['computed_etag'] = etag  # cache for success step
        return None

    def _step_success(self, ctx: SeedRunDetailContext) -> Optional[Response]:
        assert ctx.seed_run and ctx.rate_decision
        etag = ctx.request.META.get('computed_etag') or self._compute_etag(ctx.seed_run)
        body = self._serialize_seed_run(ctx.seed_run)
        body['seed_run_id'] = str(ctx.seed_run.id)
        response = Response(body, status=status.HTTP_200_OK)
        self._apply_common_headers(
            response,
            etag=etag,
            rate_limit=ctx.rate_decision,
            idempotency_key=ctx.idempotency_key,
            seed_run_id=ctx.seed_run.id,
        )
        return response

    def get(self, request: HttpRequest, seed_run_id: UUID) -> Response:
        tenant_slug, environment, idempotency_key, subject, missing = self._parse_headers(request)
        if missing:
            return self._problem_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                title='missing_headers',
                detail=f'Cabeçalhos obrigatórios ausentes: {", ".join(missing)}.',
                instance=f'/api/v1/seed-runs/{seed_run_id}',
            )

        ctx = SeedRunDetailContext(
            request=request,
            seed_run_id=seed_run_id,
            tenant_slug=str(tenant_slug),
            environment=str(environment),
            idempotency_key=idempotency_key,
            subject=subject,
        )

        steps = [
            self._step_load_tenant,
            self._step_load_seed_run,
            self._step_environment_guard,
            self._step_rbac,
            self._step_preflight,
            self._step_rate_limit,
            self._step_if_none_match,
            self._step_success,
        ]
        response = self._run_steps(ctx, steps)
        assert response is not None
        return response


class SeedRunCancelView(SeedRunViewBase):
    def _step_load_tenant(self, ctx: SeedRunCancelContext) -> Optional[Response]:
        tenant, response = self._tenant_or_response(ctx.tenant_slug, instance=f'/api/v1/seed-runs/{ctx.seed_run_id}/cancel')
        if response:
            return response
        ctx.tenant = tenant
        return None

    def _step_load_seed_run(self, ctx: SeedRunCancelContext) -> Optional[Response]:
        assert ctx.tenant
        seed_run, response = self._seed_run_or_response(
            tenant=ctx.tenant,
            seed_run_id=ctx.seed_run_id,
            instance=f'/api/v1/seed-runs/{ctx.seed_run_id}/cancel',
        )
        if response:
            return response
        ctx.seed_run = seed_run
        return None

    def _step_environment_guard(self, ctx: SeedRunCancelContext) -> Optional[Response]:
        assert ctx.seed_run
        return self._environment_guard(
            seed_run=ctx.seed_run,
            environment=str(ctx.environment),
            instance=f'/api/v1/seed-runs/{ctx.seed_run_id}/cancel',
        )

    def _step_rbac(self, ctx: SeedRunCancelContext) -> Optional[Response]:
        assert ctx.tenant
        allowed, roles = self._ensure_rbac(
            tenant_id=ctx.tenant.id,
            environment=str(ctx.environment),
            subject=ctx.subject,
            allowed_roles=['seed-admin'],
        )
        if not allowed:
            return self._problem_response(
                status_code=status.HTTP_403_FORBIDDEN,
                title='rbac_forbidden',
                detail='Somente seed-admin pode cancelar execuções.',
                instance=f'/api/v1/seed-runs/{ctx.seed_run_id}/cancel',
            )
        ctx.roles = roles
        return None

    def _step_etag_guard(self, ctx: SeedRunCancelContext) -> Optional[Response]:
        assert ctx.seed_run
        etag = self._compute_etag(ctx.seed_run)
        if_match = ctx.request.headers.get('If-Match')
        if not if_match or if_match != etag:
            return self._problem_response(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                title='etag_mismatch',
                detail='If-Match obrigatório e deve corresponder ao ETag atual.',
                instance=f'/api/v1/seed-runs/{ctx.seed_run_id}/cancel',
            )
        ctx.request.META['computed_etag'] = etag
        return None

    def _step_preflight(self, ctx: SeedRunCancelContext) -> Optional[Response]:
        assert ctx.tenant and ctx.seed_run
        return self._preflight_or_response(
            tenant=ctx.tenant,
            environment=str(ctx.environment),
            manifest_path=ctx.seed_run.manifest_path or self._manifest_path(None, ctx.tenant.slug, str(ctx.environment)),
            requested_by=ctx.subject,
            roles=ctx.roles,
            dry_run=bool(ctx.seed_run.dry_run),
        )

    def _step_rate_limit(self, ctx: SeedRunCancelContext) -> Optional[Response]:
        assert ctx.tenant and ctx.seed_run
        manifest_like = {'rate_limit': ctx.seed_run.seed_profile.rate_limit if ctx.seed_run.seed_profile else {}}
        ctx.rate_decision = self._enforce_rate_limit(
            tenant_id=ctx.tenant.id,
            environment=str(ctx.environment),
            manifest=manifest_like,
        )
        if not ctx.rate_decision.allowed:
            return self._rate_limit_response(manifest_like, ctx.rate_decision)
        return None

    def _step_idempotency(self, ctx: SeedRunCancelContext) -> Optional[Response]:
        assert ctx.tenant and ctx.seed_run
        idempo_service = SeedIdempotencyService(ctx.tenant.id, context='seed_runs_cancel')
        idempo_service.cleanup_expired(environment=str(ctx.environment))
        decision = idempo_service.ensure_entry(
            environment=str(ctx.environment),
            idempotency_key=str(ctx.idempotency_key),
            manifest_hash=ctx.seed_run.manifest_hash_sha256,
            mode=ctx.seed_run.mode,
        )
        if decision.outcome == 'conflict':
            response = self._problem_response(
                status_code=status.HTTP_409_CONFLICT,
                title='idempotency_conflict',
                detail='Idempotency-Key já usada para outro SeedRun/manifesto.',
                instance=f'/api/v1/seed-runs/{ctx.seed_run_id}/cancel',
            )
            if ctx.rate_decision:
                self._apply_rate_limit_headers(response, ctx.rate_decision)
            return response

        if decision.entry and decision.entry.seed_run_id != ctx.seed_run.id:
            with use_tenant(ctx.tenant.id):
                decision.entry.seed_run = ctx.seed_run
                decision.entry.save(update_fields=['seed_run', 'updated_at'])

        if decision.cached_response is not None:
            return decision.cached_response

        ctx.idempo_decision = decision
        ctx.idempo_service = idempo_service
        return None

    def _step_cancel(self, ctx: SeedRunCancelContext) -> Optional[Response]:
        assert ctx.seed_run and ctx.rate_decision and ctx.idempo_service and ctx.idempo_decision
        now = timezone.now()
        if ctx.seed_run.status not in {SeedRun.Status.ABORTED, SeedRun.Status.FAILED, SeedRun.Status.SUCCEEDED}:
            ctx.seed_run.status = SeedRun.Status.ABORTED
            ctx.seed_run.finished_at = now
            ctx.seed_run.reason = {
                'type': 'https://iabank.local/problems/seed/canceled',
                'title': 'seed_run_canceled',
                'detail': 'Execução cancelada via API/CLI.',
                'status': status.HTTP_202_ACCEPTED,
            }
            ctx.seed_run.save(update_fields=['status', 'finished_at', 'reason', 'updated_at'])
        self.queue_gc.release_for_run(ctx.seed_run, now=now)
        return None

    def _step_response(self, ctx: SeedRunCancelContext) -> Optional[Response]:
        assert ctx.seed_run and ctx.rate_decision and ctx.idempo_service
        etag = ctx.request.META.get('computed_etag') or self._compute_etag(ctx.seed_run)
        body = self._serialize_seed_run(ctx.seed_run)
        body['seed_run_id'] = str(ctx.seed_run.id)
        response = Response(body, status=status.HTTP_202_ACCEPTED)
        self._apply_common_headers(
            response,
            etag=etag,
            rate_limit=ctx.rate_decision,
            idempotency_key=str(ctx.idempotency_key),
            seed_run_id=ctx.seed_run.id,
        )
        ctx.idempo_service.cache_response(
            environment=str(ctx.environment),
            idempotency_key=str(ctx.idempotency_key),
            manifest_hash=ctx.seed_run.manifest_hash_sha256,
            response=response,
            context='seed_runs_cancel',
        )
        return response

    def post(self, request: HttpRequest, seed_run_id: UUID) -> Response:
        tenant_slug, environment, idempotency_key, subject, missing = self._parse_headers(request)
        if missing:
            return self._problem_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                title='missing_headers',
                detail=f'Cabeçalhos obrigatórios ausentes: {", ".join(missing)}.',
                instance=f'/api/v1/seed-runs/{seed_run_id}/cancel',
            )

        ctx = SeedRunCancelContext(
            request=request,
            seed_run_id=seed_run_id,
            tenant_slug=str(tenant_slug),
            environment=str(environment),
            idempotency_key=str(idempotency_key),
            subject=subject,
        )

        steps = [
            self._step_load_tenant,
            self._step_load_seed_run,
            self._step_environment_guard,
            self._step_rbac,
            self._step_etag_guard,
            self._step_preflight,
            self._step_rate_limit,
            self._step_idempotency,
            self._step_cancel,
            self._step_response,
        ]
        response = self._run_steps(ctx, steps)
        assert response is not None
        return response
