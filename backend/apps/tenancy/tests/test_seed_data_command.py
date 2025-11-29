from __future__ import annotations

import json
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from backend.apps.tenancy.models import EvidenceWORM, SeedCheckpoint, SeedQueue, SeedRun, Tenant
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest


def _create_tenant() -> Tenant:
    return Tenant.objects.create(
        slug='tenant-cli',
        display_name='Tenant CLI',
        primary_domain='tenant-cli.iabank.local',
        pii_policy_version='v1',
    )


def _set_preflight_env(monkeypatch: pytest.MonkeyPatch, *, enforce_worm_on_dry_run: bool = False) -> None:
    envs: dict[str, str] = {
        'VAULT_TRANSIT_PATH': 'transit/seeds/staging/tenant-cli/ff3',
        'SEEDS_WORM_BUCKET': 'worm-bucket',
        'SEEDS_WORM_ROLE_ARN': 'arn:aws:iam::123:role/worm',
        'SEEDS_WORM_KMS_KEY_ID': 'arn:aws:kms:us-east-1:123:key/worm',
        'SEEDS_WORM_RETENTION_DAYS': '365',
        'SEED_ALLOWED_ENVIRONMENTS': 'dev,homolog,staging,perf',
        'SEED_ALLOWED_ROLES': 'seed-runner,seed-admin',
        'SEED_ROLES': 'seed-runner',
        'SEED_ENFORCE_WORM_ON_DRY_RUN': 'true' if enforce_worm_on_dry_run else 'false',
    }
    for key, value in envs.items():
        monkeypatch.setenv(key, value)


@pytest.mark.django_db
def test_seed_data_command_accepts_queue_slot(capfd, monkeypatch: pytest.MonkeyPatch) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)

    call_command(
        'seed_data',
        tenant_id=str(tenant.id),
        environment='staging',
        mode='baseline',
        dry_run=True,
    )

    out = capfd.readouterr().out
    queue_entries = SeedQueue.objects.unscoped().filter(tenant=tenant).count()

    assert 'aceito na fila' in out
    assert queue_entries == 1


@pytest.mark.django_db
def test_seed_data_command_returns_conflict_when_global_cap_reached(capfd, monkeypatch: pytest.MonkeyPatch) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)
    now = timezone.now()

    SeedQueue.objects.unscoped().create(
        tenant=tenant,
        environment='staging',
        status=SeedQueue.Status.STARTED,
        enqueued_at=now,
        expires_at=now + timedelta(minutes=2),
    )
    SeedQueue.objects.unscoped().create(
        tenant=tenant,
        environment='staging',
        status=SeedQueue.Status.STARTED,
        enqueued_at=now,
        expires_at=now + timedelta(minutes=3),
    )

    with pytest.raises(SystemExit) as excinfo:
        call_command(
            'seed_data',
            tenant_id=str(tenant.id),
            environment='staging',
            mode='baseline',
        )

    err = capfd.readouterr().err
    assert excinfo.value.code == 3
    assert 'global_concurrency_cap' in err


@pytest.mark.django_db
def test_seed_data_command_returns_retry_after_when_pending_exists(capfd, monkeypatch: pytest.MonkeyPatch) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)
    now = timezone.now()

    SeedQueue.objects.unscoped().create(
        tenant=tenant,
        environment='staging',
        status=SeedQueue.Status.PENDING,
        enqueued_at=now,
        expires_at=now + timedelta(minutes=5),
    )

    with pytest.raises(SystemExit) as excinfo:
        call_command(
            'seed_data',
            tenant_id=str(tenant.id),
            environment='staging',
            mode='baseline',
        )

    err = capfd.readouterr().err
    assert excinfo.value.code == 5
    assert 'seed_queue_busy' in err


@pytest.mark.django_db
def test_seed_data_command_blocks_when_preflight_forbidden(capfd, monkeypatch: pytest.MonkeyPatch) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)

    with pytest.raises(SystemExit) as excinfo:
        call_command(
            'seed_data',
            tenant_id=str(tenant.id),
            environment='prod',  # ambiente não permitido pelo preflight
            mode='baseline',
        )

    err = capfd.readouterr().err
    assert excinfo.value.code == 1
    assert 'seed_preflight_forbidden' in err


@pytest.mark.django_db
def test_seed_data_command_dry_run_persists_seed_run_without_side_effects(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)
    manifest = build_manifest(tenant_slug=tenant.slug, environment='staging')
    manifest_path = tmp_path / 'tenant-cli.yaml'
    manifest_path.write_text(json.dumps(manifest))

    call_command(
        'seed_data',
        tenant_id=str(tenant.id),
        environment='staging',
        mode='baseline',
        dry_run=True,
        manifest_path=str(manifest_path),
    )

    runs = SeedRun.objects.filter(tenant=tenant)
    assert runs.count() == 1, 'Dry-run baseline deve registrar SeedRun para auditoria.'
    seed_run = runs.first()
    assert seed_run
    assert seed_run.dry_run is True
    assert seed_run.mode == 'baseline'
    assert SeedCheckpoint.objects.filter(tenant=tenant).count() == 0
    assert EvidenceWORM.objects.filter(tenant=tenant).count() == 0


@pytest.mark.django_db
def test_seed_data_command_blocks_cross_tenant_manifest(
    capfd,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)
    manifest = build_manifest(tenant_slug='other-tenant', environment='staging')
    manifest_path = tmp_path / 'cross-tenant.yaml'
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(SystemExit) as excinfo:
        call_command(
            'seed_data',
            tenant_id=str(tenant.id),
            environment='staging',
            mode='baseline',
            dry_run=True,
            manifest_path=str(manifest_path),
        )

    err = capfd.readouterr().err
    assert excinfo.value.code == 2
    assert 'tenant' in err.lower()
    assert SeedQueue.objects.unscoped().filter(tenant=tenant).count() == 0


@pytest.mark.django_db
def test_seed_data_command_reuses_seed_run_on_idempotent_replay(
    capfd,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)
    manifest = build_manifest(tenant_slug=tenant.slug, environment='staging')
    manifest_path = tmp_path / 'replay.yaml'
    manifest_path.write_text(json.dumps(manifest))
    idempotency_key = 'replay-key'

    call_command(
        'seed_data',
        tenant_id=str(tenant.id),
        environment='staging',
        mode='baseline',
        dry_run=True,
        manifest_path=str(manifest_path),
        idempotency_key=idempotency_key,
    )
    capfd.readouterr()  # limpa buffers antes do replay

    call_command(
        'seed_data',
        tenant_id=str(tenant.id),
        environment='staging',
        mode='baseline',
        dry_run=True,
        manifest_path=str(manifest_path),
        idempotency_key=idempotency_key,
    )

    out = capfd.readouterr().out
    assert 'Replay idempotente' in out
    assert SeedRun.objects.filter(tenant=tenant).count() == 1
    assert SeedQueue.objects.unscoped().filter(tenant=tenant).count() == 1


@pytest.mark.django_db
def test_seed_data_command_conflicts_when_idempotency_key_changes_manifest_hash(
    capfd,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)
    manifest_a = build_manifest(tenant_slug=tenant.slug, environment='staging')
    manifest_b = build_manifest(
        tenant_slug=tenant.slug,
        environment='staging',
        overrides={'metadata': {'version': '2.0.0'}},
    )
    path_a = tmp_path / 'manifest-a.yaml'
    path_b = tmp_path / 'manifest-b.yaml'
    path_a.write_text(json.dumps(manifest_a))
    path_b.write_text(json.dumps(manifest_b))
    idempotency_key = 'fixed-key'

    call_command(
        'seed_data',
        tenant_id=str(tenant.id),
        environment='staging',
        mode='baseline',
        dry_run=True,
        manifest_path=str(path_a),
        idempotency_key=idempotency_key,
    )
    capfd.readouterr()

    with pytest.raises(SystemExit) as excinfo:
        call_command(
            'seed_data',
            tenant_id=str(tenant.id),
            environment='staging',
            mode='baseline',
            dry_run=True,
            manifest_path=str(path_b),
            idempotency_key=idempotency_key,
        )

    err = capfd.readouterr().err
    assert excinfo.value.code == 2
    assert 'idempotency_conflict' in err
    assert SeedQueue.objects.unscoped().filter(tenant=tenant).count() == 1
    assert SeedRun.objects.filter(tenant=tenant).count() == 1


@pytest.mark.django_db
def test_seed_data_command_blocks_invalid_manifest_payload(
    capfd,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)
    invalid_manifest = {'metadata': {'tenant': tenant.slug, 'environment': 'staging'}}
    manifest_path = tmp_path / 'invalid.yaml'
    manifest_path.write_text(json.dumps(invalid_manifest))

    with pytest.raises(SystemExit) as excinfo:
        call_command(
            'seed_data',
            tenant_id=str(tenant.id),
            environment='staging',
            mode='baseline',
            dry_run=True,
            manifest_path=str(manifest_path),
        )

    err = capfd.readouterr().err
    assert excinfo.value.code == 2
    assert 'manifest_invalid' in err
    assert SeedQueue.objects.unscoped().filter(tenant=tenant).count() == 0
    assert SeedRun.objects.filter(tenant=tenant).count() == 0
