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


@pytest.mark.django_db
def test_seed_data_command_accepts_queue_slot(capfd) -> None:
    tenant = _create_tenant()

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
def test_seed_data_command_returns_conflict_when_global_cap_reached(capfd) -> None:
    tenant = _create_tenant()
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
def test_seed_data_command_returns_retry_after_when_pending_exists(capfd) -> None:
    tenant = _create_tenant()
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
