from __future__ import annotations

import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Mapping, Optional
from urllib.parse import urlparse

from backend.apps.tenancy.services.seed_runs import ProblemDetail

DEFAULT_ALLOWED_HOSTS = ('localhost', '127.0.0.1', 'pact', 'prism', 'stub')


@dataclass(frozen=True)
class IntegrationConfig:
    kyc_url: str
    antifraud_url: str
    pagamentos_url: str
    notificacoes_url: str
    allowed_hosts: tuple[str, ...] = DEFAULT_ALLOWED_HOSTS


class SeedIntegrationService:
    """
    Garante que integrações externas usem stubs Pact/Prism (nenhum outbound real).
    """

    def __init__(self, config: IntegrationConfig | None = None) -> None:
        self.config = config or self.from_env()

    @classmethod
    def from_env(cls) -> IntegrationConfig:
        base_stub = os.getenv('SEED_STUB_BASE', 'http://localhost:4010')
        raw_allowed = os.getenv('SEED_OUTBOUND_ALLOWLIST', ','.join(DEFAULT_ALLOWED_HOSTS))
        allowed_hosts = tuple(host.strip() for host in raw_allowed.split(',') if host.strip()) or DEFAULT_ALLOWED_HOSTS

        return IntegrationConfig(
            kyc_url=os.getenv('SEED_KYC_URL', f'{base_stub}/kyc'),
            antifraud_url=os.getenv('SEED_ANTIFRAUDE_URL', f'{base_stub}/antifraude'),
            pagamentos_url=os.getenv('SEED_PAGAMENTOS_URL', f'{base_stub}/pagamentos'),
            notificacoes_url=os.getenv('SEED_NOTIFICACOES_URL', f'{base_stub}/notificacoes'),
            allowed_hosts=allowed_hosts,
        )

    def endpoints_from_manifest(self, manifest: Mapping[str, Any] | None) -> dict[str, str]:
        if manifest and isinstance(manifest, Mapping):
            raw = manifest.get('integrations') or {}
            if isinstance(raw, Mapping):
                return {
                    'kyc': str(raw.get('kyc') or self.config.kyc_url),
                    'antifraude': str(raw.get('antifraude') or self.config.antifraud_url),
                    'pagamentos': str(raw.get('pagamentos') or self.config.pagamentos_url),
                    'notificacoes': str(raw.get('notificacoes') or self.config.notificacoes_url),
                }

        return {
            'kyc': self.config.kyc_url,
            'antifraude': self.config.antifraud_url,
            'pagamentos': self.config.pagamentos_url,
            'notificacoes': self.config.notificacoes_url,
        }

    def block_outbound(self, *, manifest: Mapping[str, Any] | None = None) -> Optional[ProblemDetail]:
        endpoints = self.endpoints_from_manifest(manifest)
        for name, url in endpoints.items():
            parsed = urlparse(url)
            host = parsed.hostname or ''
            if not host or not self._is_allowed_host(host):
                return ProblemDetail(
                    status=HTTPStatus.SERVICE_UNAVAILABLE,
                    title='external_calls_blocked',
                    detail=f'Integração {name} aponta para host não permitido ({host or "desconhecido"}); use stubs Pact/Prism.',
                    type='https://iabank.local/problems/seed/outbound-blocked',
                )
        return None

    def _is_allowed_host(self, host: str) -> bool:
        normalized = host.lower()
        return any(allowed in normalized for allowed in self.config.allowed_hosts)
