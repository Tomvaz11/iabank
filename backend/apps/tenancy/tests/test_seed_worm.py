from __future__ import annotations

from datetime import time
from decimal import Decimal
from http import HTTPStatus
from pathlib import Path

import pytest
from django.utils import timezone

from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import EvidenceWORM, SeedProfile, SeedRun, Tenant
from backend.apps.tenancy.services.seed_worm import InMemoryWormStorage, LocalWormSigner, SeedWormService


class RejectSigner(LocalWormSigner):
    def verify(self, *, digest: str, signature) -> bool:  # type: ignore[override]
        return False


def _create_seed_run(*, mode: str = 'carga', dry_run: bool = False) -> tuple[Tenant, SeedRun]:
    tenant = Tenant.objects.create(
        slug=f'tenant-worm-{mode}',
        display_name='Tenant WORM',
        primary_domain=f'{mode}.iabank.local',
        pii_policy_version='v1',
    )
    reference_dt = timezone.now()
    with use_tenant(tenant.id):
        profile = SeedProfile.objects.create(
            tenant=tenant,
            environment='staging',
            profile='default',
            schema_version='v1',
            version='1.0.0',
            mode=mode,
            reference_datetime=reference_dt,
            volumetry={},
            rate_limit={'limit': 10, 'window_seconds': 60},
            backoff={'base_seconds': 1, 'jitter_factor': 0.1, 'max_retries': 3, 'max_interval_seconds': 30},
            budget={'cost_cap_brl': 10, 'error_budget_pct': 5},
            window_start_utc=time.fromisoformat('00:00'),
            window_end_utc=time.fromisoformat('06:00'),
            ttl_config={'baseline_days': 0, 'carga_days': 1, 'dr_days': 1},
            slo_p95_ms=120,
            slo_p99_ms=240,
            slo_throughput_rps=Decimal('1.5'),
            integrity_hash='seed-manifest-hash',
            manifest_path='configs/seed_profiles/staging/tenant-worm.yaml',
            manifest_hash_sha256='seed-manifest-hash',
            salt_version='v1',
            canary_scope=None,
        )
        seed_run = SeedRun.objects.create(
            tenant=tenant,
            seed_profile=profile,
            environment=profile.environment,
            mode=profile.mode,
            status=SeedRun.Status.RUNNING,
            requested_by='tester',
            idempotency_key='idempo-worm',
            manifest_path=profile.manifest_path,
            manifest_hash_sha256=profile.manifest_hash_sha256,
            reference_datetime=reference_dt,
            trace_id='trace-worm',
            span_id='span-worm',
            rate_limit_usage={'limit': 10, 'remaining': 9, 'reset_at': reference_dt.isoformat()},
            profile_version=profile.version,
            dry_run=dry_run,
            offpeak_window={'start': '00:00', 'end': '06:00'},
        )
    return tenant, seed_run


@pytest.mark.django_db
def test_emit_skips_when_dry_run() -> None:
    _, seed_run = _create_seed_run(dry_run=True)
    service = SeedWormService(enforce_on_dry_run=False)

    outcome = service.emit(
        seed_run=seed_run,
        manifest={'integrity': {'manifest_hash': 'seed-manifest-hash'}},
        checklist_results={'pii_masked': True},
        retention_days=365,
        cost_estimated_brl=0,
        cost_actual_brl=0,
        cost_model_version='v1',
        extra_metadata={},
    )

    assert outcome.problem is None
    assert outcome.evidence is None
    assert outcome.report['status'] == 'skipped'


@pytest.mark.django_db
def test_emit_blocks_when_retention_below_minimum() -> None:
    _, seed_run = _create_seed_run()
    service = SeedWormService(min_retention_days=365, enforce_on_dry_run=True)

    outcome = service.emit(
        seed_run=seed_run,
        manifest={},
        checklist_results={'pii_masked': True},
        retention_days=120,
        cost_estimated_brl=0,
        cost_actual_brl=0,
        cost_model_version='v1',
        extra_metadata={},
    )

    assert outcome.evidence is None
    assert outcome.report == {}
    assert outcome.problem and outcome.problem.status == HTTPStatus.SERVICE_UNAVAILABLE


@pytest.mark.django_db
def test_emit_persists_report_and_signature() -> None:
    tenant, seed_run = _create_seed_run()
    storage = InMemoryWormStorage()
    service = SeedWormService(storage=storage, signer=LocalWormSigner(), enforce_on_dry_run=True)

    outcome = service.emit(
        seed_run=seed_run,
        manifest={'integrity': {'manifest_hash': 'seed-manifest-hash'}},
        checklist_results={
            'pii_masked': True,
            'rls_enforced': True,
            'contracts_aligned': True,
            'idempotency_reused': True,
            'rate_limit_respected': True,
            'slo_met': True,
        },
        retention_days=400,
        cost_estimated_brl=12.34,
        cost_actual_brl=10.00,
        cost_model_version='2025.01',
        extra_metadata={'commit': 'abc123'},
    )

    assert outcome.problem is None
    assert outcome.evidence is not None
    assert outcome.evidence.integrity_status == EvidenceWORM.IntegrityStatus.VERIFIED
    assert outcome.report['checklist']['summary']['failed'] == 0
    stored = storage.retrieve(outcome.evidence.report_url)
    assert stored
    assert tenant.id == outcome.evidence.tenant_id


@pytest.mark.django_db
def test_emit_returns_problem_when_checklist_fails() -> None:
    _, seed_run = _create_seed_run()
    storage = InMemoryWormStorage()
    service = SeedWormService(storage=storage, enforce_on_dry_run=True)

    outcome = service.emit(
        seed_run=seed_run,
        manifest={},
        checklist_results={'pii_masked': False, 'rls_enforced': True},
        retention_days=365,
        cost_estimated_brl=0,
        cost_actual_brl=0,
        cost_model_version='v1',
        extra_metadata={},
    )

    assert outcome.problem is not None
    assert outcome.problem.title == 'worm_checklist_failed'
    assert outcome.report['status'] == 'failed'
    assert outcome.evidence is not None


@pytest.mark.django_db
def test_emit_returns_problem_when_signature_invalid() -> None:
    _, seed_run = _create_seed_run()
    storage = InMemoryWormStorage()
    service = SeedWormService(storage=storage, signer=RejectSigner(), enforce_on_dry_run=True)

    outcome = service.emit(
        seed_run=seed_run,
        manifest={'integrity': {'manifest_hash': 'seed-manifest-hash'}},
        checklist_results={'pii_masked': True, 'rls_enforced': True},
        retention_days=365,
        cost_estimated_brl=0,
        cost_actual_brl=0,
        cost_model_version='v1',
        extra_metadata={},
    )

    assert outcome.problem is not None
    assert outcome.problem.title == 'worm_integrity_failed'
    assert outcome.evidence is not None
    assert outcome.evidence.integrity_status == EvidenceWORM.IntegrityStatus.INVALID


@pytest.mark.django_db
def test_fallback_checklist_used_when_template_missing() -> None:
    _, seed_run = _create_seed_run()
    missing_path = Path('/tmp/seed-worm-checklist-missing.json')
    if missing_path.exists():
        missing_path.unlink()

    service = SeedWormService(
        storage=InMemoryWormStorage(),
        signer=LocalWormSigner(),
        enforce_on_dry_run=True,
        checklist_path=missing_path,
    )
    all_true_results = {item['id']: True for item in service.checklist_template}

    outcome = service.emit(
        seed_run=seed_run,
        manifest={'integrity': {'manifest_hash': 'seed-manifest-hash'}},
        checklist_results=all_true_results,
        retention_days=365,
        cost_estimated_brl=1.0,
        cost_actual_brl=0.5,
        cost_model_version='v1',
        extra_metadata={},
    )

    assert outcome.problem is None
    assert outcome.report['checklist']['summary']['failed'] == 0
    assert len(outcome.report['checklist']['items']) == len(service.checklist_template)
