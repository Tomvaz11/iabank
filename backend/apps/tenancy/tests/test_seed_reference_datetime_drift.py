from __future__ import annotations

import json
from datetime import time
from typing import Any, Dict

import pytest
from django.core.management import call_command
from django.utils.dateparse import parse_datetime

from backend.apps.tenancy.models import SeedCheckpoint, SeedProfile, SeedQueue, SeedRun, Tenant
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest, compute_manifest_hash


def _create_tenant() -> Tenant:
    return Tenant.objects.create(
        slug='tenant-seed',
        display_name='Tenant Seed',
        primary_domain='tenant-seed.iabank.local',
        pii_policy_version='v1',
    )


def _set_preflight_env(monkeypatch: pytest.MonkeyPatch) -> None:
    envs: dict[str, str] = {
        'VAULT_TRANSIT_PATH': 'transit/seeds/staging/tenant-seed/ff3',
        'SEEDS_WORM_BUCKET': 'worm-bucket',
        'SEEDS_WORM_ROLE_ARN': 'arn:aws:iam::123:role/worm',
        'SEEDS_WORM_KMS_KEY_ID': 'arn:aws:kms:us-east-1:123:key/worm',
        'SEEDS_WORM_RETENTION_DAYS': '365',
        'SEED_ALLOWED_ENVIRONMENTS': 'dev,homolog,staging,perf',
        'SEED_ALLOWED_ROLES': 'seed-runner,seed-admin',
    }
    for key, value in envs.items():
        monkeypatch.setenv(key, value)


def _create_seed_profile(*, tenant: Tenant, manifest: Dict[str, Any]) -> SeedProfile:
    reference_dt = parse_datetime(manifest['reference_datetime'])
    assert reference_dt is not None
    window = manifest.get('window', {})
    start = time.fromisoformat(str(window.get('start_utc', '00:00')))
    end = time.fromisoformat(str(window.get('end_utc', '06:00')))
    return SeedProfile.objects.create(
        tenant=tenant,
        environment=manifest['metadata']['environment'],
        profile=manifest['metadata']['profile'],
        schema_version=manifest['metadata']['schema_version'],
        version=manifest['metadata']['version'],
        mode=manifest['mode'],
        reference_datetime=reference_dt,
        volumetry=manifest['volumetry'],
        rate_limit=manifest['rate_limit'],
        backoff=manifest['backoff'],
        budget=manifest['budget'],
        window_start_utc=start,
        window_end_utc=end,
        ttl_config=manifest['ttl'],
        slo_p95_ms=manifest['slo']['p95_target_ms'],
        slo_p99_ms=manifest['slo']['p99_target_ms'],
        slo_throughput_rps=manifest['slo']['throughput_target_rps'],
        integrity_hash=manifest['integrity']['manifest_hash'],
        manifest_path=f"configs/seed_profiles/{manifest['metadata']['environment']}/{tenant.slug}.yaml",
        manifest_hash_sha256=compute_manifest_hash(manifest),
        salt_version=manifest['metadata']['salt_version'],
    )


@pytest.mark.django_db
def test_seed_data_blocks_reference_datetime_drift(
    capfd,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)
    base_manifest = build_manifest(tenant_slug=tenant.slug, environment='staging')
    drifted_manifest = build_manifest(
        tenant_slug=tenant.slug,
        environment='staging',
        overrides={'reference_datetime': '2025-02-01T00:00:00Z'},
    )
    manifest_path = tmp_path / 'manifest-drift.yaml'
    manifest_path.write_text(json.dumps(drifted_manifest))

    seed_profile = _create_seed_profile(tenant=tenant, manifest=base_manifest)
    reference_dt = parse_datetime(base_manifest['reference_datetime'])
    assert reference_dt is not None
    seed_run = SeedRun.objects.create(
        tenant=tenant,
        seed_profile=seed_profile,
        environment='staging',
        mode='baseline',
        status=SeedRun.Status.SUCCEEDED,
        requested_by='cli:seed-data',
        idempotency_key='initial-run',
        manifest_path='configs/seed_profiles/staging/tenant-seed.yaml',
        manifest_hash_sha256=compute_manifest_hash(base_manifest),
        reference_datetime=reference_dt,
        profile_version=base_manifest['metadata']['version'],
        dry_run=False,
    )
    SeedCheckpoint.objects.create(
        tenant=tenant,
        seed_run=seed_run,
        entity='customers',
        hash_estado='hash-base',
        resume_token=b'stable',
        percentual_concluido=50,
        sealed=False,
    )

    with pytest.raises(SystemExit) as excinfo:
        call_command(
            'seed_data',
            tenant_id=str(tenant.id),
            environment='staging',
            mode='baseline',
            manifest_path=str(manifest_path),
        )

    err = capfd.readouterr().err
    assert excinfo.value.code == 2
    assert 'reference_datetime' in err.lower() or 'checkpoint' in err.lower()
    assert SeedQueue.objects.unscoped().filter(tenant=tenant).count() == 0
