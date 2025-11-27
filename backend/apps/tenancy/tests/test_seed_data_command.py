from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from backend.apps.tenancy.models import SeedQueue, Tenant


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
