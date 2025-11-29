from __future__ import annotations

import hashlib
from dataclasses import dataclass


def derive_factory_seed(tenant_id: str, environment: str, manifest_version: str, salt_version: str) -> int:
    """
    Gera um seed determinístico a partir do contexto do manifesto para uso em factories/tests.
    """
    raw = "|".join([tenant_id.strip(), environment.strip(), manifest_version.strip(), salt_version.strip()])
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def build_idempotency_fingerprint(
    tenant_id: str,
    environment: str,
    idempotency_key: str,
    manifest_hash: str,
) -> str:
    """
    Normaliza os parâmetros de idempotência e devolve um hash estável (sha256 hex).
    """
    normalized = "|".join(
        [
            tenant_id.strip(),
            environment.strip(),
            idempotency_key.strip(),
            manifest_hash.strip(),
        ],
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class VaultTransitFPEClient:
    """
    Cliente simplificado para Vault Transit FPE.

    Em ambientes sem Vault, utiliza um mascaramento determinístico baseado em hash
    apenas para preservar formato/tamanho e permitir TDD das factories.
    """

    transit_path: str
    salt_namespace: str = "seed-data"
    allow_stub_decrypt: bool = False

    def _hash(self, value: str, salt_version: str) -> str:
        payload = f"{self.transit_path}:{self.salt_namespace}:{salt_version}:{value}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def mask(self, value: str, *, salt_version: str) -> str:
        if value is None:
            return value
        digest = self._hash(value, salt_version)
        # Repete o digest para manter o comprimento do campo original.
        return (digest * ((len(value) // len(digest)) + 1))[: len(value)]

    def unmask(self, value: str, *, salt_version: str) -> str:
        if self.allow_stub_decrypt:
            return value
        raise NotImplementedError(
            "Vault Transit FPE real não está configurado; configure allow_stub_decrypt=True ou injete cliente real.",
        )
