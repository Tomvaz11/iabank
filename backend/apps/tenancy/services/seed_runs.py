from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal
from http import HTTPStatus
from typing import Any, Dict, Optional
from uuid import UUID

from django.db import connection, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedBatch, SeedCheckpoint, SeedProfile, SeedRun
from backend.apps.tenancy.services.seed_manifest_validator import (
    SeedManifestValidator,
    compute_manifest_hash,
)
from backend.apps.tenancy.services.seed_queue import QueueDecision, SeedQueueService


@dataclass
class ProblemDetail:
    status: int
    title: str
    detail: str
    type: str
    retry_after: Optional[int] = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            'status': self.status,
            'title': self.title,
            'detail': self.detail,
            'type': self.type,
        }
        if self.retry_after is not None:
            payload['retry_after'] = self.retry_after
        return payload


@dataclass
class SeedRunCreation:
    seed_run: SeedRun
    seed_profile: SeedProfile
    batches: list[SeedBatch]


class SeedRunService:
    def __init__(self, queue_service: Optional[SeedQueueService] = None) -> None:
        self.queue_service = queue_service or SeedQueueService()

    def ensure_reference_drift(
        self,
        *,
        tenant_id: UUID,
        environment: str,
        mode: str,
        reference_datetime: datetime,
    ) -> Optional[ProblemDetail]:
        """
        Bloqueia execução quando já existem checkpoints para um reference_datetime diferente.
        """
        with use_tenant(tenant_id):
            checkpoints = (
                SeedCheckpoint.objects.select_related('seed_run')
                .filter(seed_run__environment=environment, seed_run__mode=mode)
                .all()
            )

        for checkpoint in checkpoints:
            run = checkpoint.seed_run
            if run and run.reference_datetime != reference_datetime:
                return ProblemDetail(
                    status=HTTPStatus.UNPROCESSABLE_ENTITY,
                    title='reference_datetime_drift',
                    detail=(
                        'Reference datetime do manifesto diverge de checkpoints existentes. '
                        'Limpe checkpoints/seed datasets antes de forçar novo seed_data.'
                    ),
                    type='https://iabank.local/problems/seed/reference-drift',
                )
        return None

    def create_seed_run(
        self,
        *,
        tenant_id: UUID,
        environment: str,
        manifest: Dict[str, Any],
        manifest_path: str,
        idempotency_key: str,
        requested_by: str,
        dry_run: bool,
        mode: str,
    ) -> SeedRunCreation:
        manifest_hash = compute_manifest_hash(manifest)
        reference_datetime = self._parse_reference_datetime(manifest)
        window_start, window_end = self._extract_window(manifest)
        volumetry = manifest.get('volumetry') if isinstance(manifest, dict) else {}
        rate_limit = manifest.get('rate_limit') if isinstance(manifest, dict) else {}
        backoff = manifest.get('backoff') if isinstance(manifest, dict) else {}
        budget = manifest.get('budget') if isinstance(manifest, dict) else {}
        ttl_config = manifest.get('ttl') if isinstance(manifest, dict) else {}
        slo = manifest.get('slo') if isinstance(manifest, dict) else {}
        integrity = manifest.get('integrity') if isinstance(manifest, dict) else {}
        metadata = manifest.get('metadata') if isinstance(manifest, dict) else {}
        canary_scope = manifest.get('canary') if isinstance(manifest, dict) else None

        with transaction.atomic():
            if not self._acquire_advisory_lock(tenant_id, environment):
                raise RuntimeError('Não foi possível adquirir lock para o seed_data.')  # pragma: no cover

            with use_tenant(tenant_id):
                seed_profile, _ = SeedProfile.objects.update_or_create(
                    profile=metadata.get('profile', 'default'),
                    version=metadata.get('version', '0.0.0'),
                    defaults={
                        'environment': environment,
                        'schema_version': metadata.get('schema_version', 'v1'),
                        'mode': mode,
                        'reference_datetime': reference_datetime,
                        'volumetry': volumetry or {},
                        'rate_limit': rate_limit or {},
                        'backoff': backoff or {},
                        'budget': budget or {},
                        'window_start_utc': window_start,
                        'window_end_utc': window_end,
                        'ttl_config': ttl_config or {},
                        'slo_p95_ms': int(slo.get('p95_target_ms', 0) or 0),
                        'slo_p99_ms': int(slo.get('p99_target_ms', 0) or 0),
                        'slo_throughput_rps': Decimal(str(slo.get('throughput_target_rps', 0) or 0)),
                        'integrity_hash': integrity.get('manifest_hash', manifest_hash),
                        'manifest_path': manifest_path,
                        'manifest_hash_sha256': manifest_hash,
                        'salt_version': metadata.get('salt_version', 'v1'),
                        'canary_scope': canary_scope,
                    },
                )

                seed_run = SeedRun.objects.create(
                    seed_profile=seed_profile,
                    environment=environment,
                    mode=mode,
                    status=SeedRun.Status.QUEUED,
                    requested_by=requested_by,
                    idempotency_key=idempotency_key,
                    manifest_path=manifest_path,
                    manifest_hash_sha256=manifest_hash,
                    reference_datetime=reference_datetime,
                    profile_version=metadata.get('version', ''),
                    dry_run=dry_run,
                    offpeak_window={'start': window_start.isoformat(), 'end': window_end.isoformat()},
                    canary_scope_snapshot=canary_scope,
                )

                batches = self._create_batches(seed_run, volumetry or {})

        return SeedRunCreation(seed_run=seed_run, seed_profile=seed_profile, batches=batches)

    def request_slot(
        self,
        *,
        environment: str,
        tenant_id: UUID,
        seed_run_id: Optional[UUID] = None,
        now: Optional[datetime] = None,
    ) -> tuple[QueueDecision, Optional[ProblemDetail]]:
        current_time = now or timezone.now()
        decision = self.queue_service.enqueue(
            environment=environment,
            tenant_id=tenant_id,
            seed_run_id=seed_run_id,
            now=current_time,
        )

        if decision.allowed:
            return decision, None

        return decision, self._build_problem(decision=decision, environment=environment)

    @staticmethod
    def exit_code_for(decision: QueueDecision) -> int:
        if decision.status_code == HTTPStatus.CONFLICT:
            return 3
        if decision.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            return 5
        return 1

    @staticmethod
    def _build_problem(decision: QueueDecision, environment: str) -> ProblemDetail:
        if decision.status_code == HTTPStatus.CONFLICT:
            return ProblemDetail(
                status=HTTPStatus.CONFLICT,
                title='global_concurrency_cap',
                detail=f'Limite global de execuções ativas atingido no ambiente {environment}.',
                type='https://iabank.local/problems/seed/global-cap',
                retry_after=decision.retry_after,
            )

        return ProblemDetail(
            status=HTTPStatus.TOO_MANY_REQUESTS,
            title='seed_queue_busy',
            detail=f'A fila de seeds do ambiente {environment} ainda possui itens pendentes dentro do TTL.',
            type='https://iabank.local/problems/seed/queue-ttl',
            retry_after=decision.retry_after,
        )

    @staticmethod
    def exit_code_for_problem(problem: ProblemDetail) -> int:
        if problem.status in {HTTPStatus.BAD_REQUEST, HTTPStatus.UNPROCESSABLE_ENTITY, HTTPStatus.CONFLICT}:
            return 2
        if problem.status == HTTPStatus.TOO_MANY_REQUESTS:
            return 5
        return 1

    @staticmethod
    def _parse_reference_datetime(manifest: Dict[str, Any]) -> datetime:
        raw = manifest.get('reference_datetime') if isinstance(manifest, dict) else None
        parsed = parse_datetime(str(raw)) if raw is not None else None
        return parsed or timezone.now()

    @staticmethod
    def _extract_window(manifest: Dict[str, Any]) -> tuple[time, time]:
        window = manifest.get('window') if isinstance(manifest, dict) else {}
        start_raw = window.get('start_utc', '00:00')
        end_raw = window.get('end_utc', '06:00')
        try:
            start = time.fromisoformat(str(start_raw))
        except ValueError:
            start = time.fromisoformat('00:00')
        try:
            end = time.fromisoformat(str(end_raw))
        except ValueError:
            end = time.fromisoformat('06:00')
        return start, end

    @staticmethod
    def _create_batches(seed_run: SeedRun, volumetry: Dict[str, Any]) -> list[SeedBatch]:
        ordered_entities = [
            'tenant_users',
            'customers',
            'addresses',
            'consultants',
            'bank_accounts',
            'account_categories',
            'suppliers',
            'loans',
            'installments',
            'financial_transactions',
            'limits',
            'contracts',
        ]

        batches: list[SeedBatch] = []
        volumetry_caps = SeedManifestValidator.extract_caps({'volumetry': volumetry})

        for entity in ordered_entities:
            cap = volumetry_caps.get(entity)
            if cap is None:
                continue
            snapshot = volumetry.get(entity, {}) if isinstance(volumetry, dict) else {}
            batches.append(
                SeedBatch(
                    seed_run=seed_run,
                    tenant=seed_run.tenant,
                    entity=entity,
                    batch_size=max(1, int(cap)),
                    caps_snapshot=snapshot,
                )
            )

        with use_tenant(seed_run.tenant_id):
            SeedBatch.objects.bulk_create(batches)
        return batches

    @staticmethod
    def _acquire_advisory_lock(tenant_id: UUID, environment: str) -> bool:
        """
        Serializa criação de SeedRun por tenant/ambiente usando pg_try_advisory_xact_lock.
        """
        key = abs(hash((str(tenant_id), environment))) % (2**63)
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_try_advisory_xact_lock(%s)', [key])
            locked = cursor.fetchone()
        return bool(locked and locked[0])
