from __future__ import annotations

import json
from http import HTTPStatus

import pytest
from django.core.management import call_command

from backend.apps.tenancy.services.seed_integrations import IntegrationConfig, SeedIntegrationService
from backend.apps.tenancy.tests.test_seed_data_command import _create_tenant, _set_preflight_env
from backend.apps.tenancy.tests.seed_profile_test_utils import build_manifest


def test_seed_integration_service_blocks_real_hosts() -> None:
    config = IntegrationConfig(
        kyc_url='https://kyc.real.example.com/api/v1/check',
        antifraud_url='http://localhost:4010/antifraude',
        pagamentos_url='http://localhost:4011/pagamentos',
        notificacoes_url='http://localhost:4012/notificacoes',
    )
    service = SeedIntegrationService(config=config)

    problem = service.block_outbound()

    assert problem is not None
    assert problem.status == HTTPStatus.SERVICE_UNAVAILABLE
    assert 'external_calls_blocked' in problem.title


def test_seed_integration_service_accepts_stub_hosts() -> None:
    config = IntegrationConfig(
        kyc_url='http://localhost:4010/kyc',
        antifraud_url='http://127.0.0.1:4011/antifraude',
        pagamentos_url='http://prism:4012/pagamentos',
        notificacoes_url='http://pact:4013/notificacoes',
    )
    service = SeedIntegrationService(config=config)

    assert service.block_outbound() is None


@pytest.mark.django_db
def test_seed_data_command_blocks_real_outbound(monkeypatch: pytest.MonkeyPatch, capfd, tmp_path) -> None:
    tenant = _create_tenant()
    _set_preflight_env(monkeypatch)
    manifest = build_manifest(tenant_slug=tenant.slug, environment='staging')
    manifest_path = tmp_path / 'manifest-outbound.json'
    manifest_path.write_text(json.dumps(manifest))

    monkeypatch.setenv('SEED_KYC_URL', 'https://kyc.real.example.com')
    monkeypatch.setenv('SEED_ANTIFRAUDE_URL', 'https://fraude.example.com')
    monkeypatch.setenv('SEED_PAGAMENTOS_URL', 'https://pagamentos.example.com')

    with pytest.raises(SystemExit) as excinfo:
        call_command(
            'seed_data',
            tenant_id=str(tenant.id),
            environment='staging',
            mode='baseline',
            manifest_path=str(manifest_path),
        )

    err = capfd.readouterr().err
    assert excinfo.value.code == 1
    assert 'external_calls_blocked' in err
