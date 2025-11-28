from __future__ import annotations

from datetime import time, timedelta
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.utils import timezone

from backend.apps.tenancy.feature_flags import SeedDORAMetrics, SeedFeatureFlags
from backend.apps.tenancy.managers import use_tenant
from backend.apps.tenancy.models import SeedProfile, SeedRun, Tenant


def _create_seed_profile(tenant: Tenant, *, mode: str) -> SeedProfile:
    reference_dt = timezone.now()
    with use_tenant(tenant.id):
        return SeedProfile.objects.create(
            tenant=tenant,
            environment='staging',
            profile=f'{mode}-profile',
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


@pytest.mark.django_db
def test_canary_scope_requires_canary_mode() -> None:
    flags = SeedFeatureFlags()

    problem = flags.ensure_canary_scope(manifest={'canary': {'percentage': 10}}, mode='baseline')

    assert problem is not None
    assert problem.status == HTTPStatus.FORBIDDEN
    assert 'canary' in problem.detail


@pytest.mark.django_db
def test_canary_scope_allows_canary_mode() -> None:
    flags = SeedFeatureFlags()

    problem = flags.ensure_canary_scope(manifest={'canary': {'percentage': 10}}, mode='canary')

    assert problem is None


@pytest.mark.django_db
def test_dora_metrics_snapshot_tracks_failure_rate_and_mttr() -> None:
    tenant = Tenant.objects.create(
        slug='tenant-dora',
        display_name='Tenant DORA',
        primary_domain='dora.iabank.local',
        pii_policy_version='v1',
    )
    now = timezone.now()
    success_profile = _create_seed_profile(tenant, mode='baseline')
    fail_profile = _create_seed_profile(tenant, mode='carga')
    dr_profile = _create_seed_profile(tenant, mode='dr')

    with use_tenant(tenant.id):
        SeedRun.objects.create(
            tenant=tenant,
            seed_profile=success_profile,
            environment='staging',
            mode='baseline',
            status=SeedRun.Status.SUCCEEDED,
            requested_by='tester',
            idempotency_key='idempo-success',
            manifest_path=success_profile.manifest_path,
            manifest_hash_sha256=success_profile.manifest_hash_sha256,
            reference_datetime=now,
            trace_id='trace-success',
            span_id='span-success',
            rate_limit_usage={},
            profile_version=success_profile.version,
            dry_run=False,
            offpeak_window={'start': '00:00', 'end': '06:00'},
            started_at=now,
            finished_at=now + timedelta(minutes=10),
        )
        failed_run = SeedRun.objects.create(
            tenant=tenant,
            seed_profile=fail_profile,
            environment='staging',
            mode='carga',
            status=SeedRun.Status.FAILED,
            requested_by='tester',
            idempotency_key='idempo-fail',
            manifest_path=fail_profile.manifest_path,
            manifest_hash_sha256=fail_profile.manifest_hash_sha256,
            reference_datetime=now,
            trace_id='trace-fail',
            span_id='span-fail',
            rate_limit_usage={},
            profile_version=fail_profile.version,
            dry_run=False,
            offpeak_window={'start': '00:00', 'end': '06:00'},
            started_at=now,
            finished_at=now + timedelta(minutes=25),
        )
        SeedRun.objects.create(
            tenant=tenant,
            seed_profile=dr_profile,
            environment='staging',
            mode='dr',
            status=SeedRun.Status.BLOCKED,
            requested_by='tester',
            idempotency_key='idempo-dr',
            manifest_path=dr_profile.manifest_path,
            manifest_hash_sha256=dr_profile.manifest_hash_sha256,
            reference_datetime=now,
            trace_id='trace-dr',
            span_id='span-dr',
            rate_limit_usage={},
            profile_version=dr_profile.version,
            dry_run=False,
            offpeak_window={'start': '00:00', 'end': '06:00'},
            started_at=now,
            finished_at=now + timedelta(minutes=35),
        )

    metrics = SeedDORAMetrics(window_days=7).snapshot(seed_run=failed_run)

    assert metrics['deployments'] == 3
    assert metrics['rollback_rehearsed'] is True
    assert metrics['deployment_frequency_per_day'] == pytest.approx(3 / 7, rel=1e-4)
    assert metrics['change_failure_rate'] == pytest.approx(2 / 3, rel=1e-4)
    assert metrics['mttr_minutes'] == pytest.approx((25 + 35) / 2, rel=1e-4)
    assert metrics['lead_time_minutes'] == pytest.approx(10, rel=1e-4)
