from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional, Sequence

from backend.apps.tenancy.services.worm_retention import MIN_WORM_RETENTION_DAYS


@dataclass
class PreflightContext:
    tenant_id: str
    environment: str
    manifest_path: str
    requested_by: str
    roles: Sequence[str]
    dry_run: bool = False


@dataclass
class SeedPreflightConfig:
    vault_transit_path: str
    worm_bucket: str
    worm_role_arn: str
    worm_kms_key_id: str
    worm_retention_days: int
    allowed_roles: set[str]
    allowed_environments: set[str]
    enforce_worm_on_dry_run: bool = False

    @classmethod
    def from_env(cls) -> "SeedPreflightConfig":
        return cls(
            vault_transit_path=os.getenv("VAULT_TRANSIT_PATH", ""),
            worm_bucket=os.getenv("SEEDS_WORM_BUCKET", ""),
            worm_role_arn=os.getenv("SEEDS_WORM_ROLE_ARN", ""),
            worm_kms_key_id=os.getenv("SEEDS_WORM_KMS_KEY_ID", ""),
            worm_retention_days=int(os.getenv("SEEDS_WORM_RETENTION_DAYS", str(MIN_WORM_RETENTION_DAYS))),
            allowed_roles=set(os.getenv("SEED_ALLOWED_ROLES", "seed-runner,seed-admin").split(",")),
            allowed_environments=set(
                os.getenv("SEED_ALLOWED_ENVIRONMENTS", "dev,homolog,staging,perf").split(","),
            ),
            enforce_worm_on_dry_run=os.getenv("SEED_ENFORCE_WORM_ON_DRY_RUN", "false").lower() == "true",
        )


@dataclass
class ProblemDetail:
    status: int
    title: str
    detail: str
    type: str

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "title": self.title,
            "detail": self.detail,
            "type": self.type,
        }


@dataclass
class PreflightResult:
    allowed: bool
    audit: dict[str, object]
    problem: Optional[ProblemDetail] = None


class SeedPreflightService:
    def __init__(
        self,
        config: Optional[SeedPreflightConfig] = None,
        *,
        min_worm_retention_days: int = MIN_WORM_RETENTION_DAYS,
    ) -> None:
        self.config = config or SeedPreflightConfig.from_env()
        self.min_worm_retention_days = min_worm_retention_days

    def check(self, context: PreflightContext) -> PreflightResult:
        audit = self._build_audit(context)

        rbac_problem = self._validate_rbac(context)
        if rbac_problem:
            return PreflightResult(allowed=False, audit=audit, problem=rbac_problem)

        vault_problem = self._validate_vault(audit)
        if vault_problem:
            return PreflightResult(allowed=False, audit=audit, problem=vault_problem)

        worm_problem = self._validate_worm(context, audit)
        if worm_problem:
            return PreflightResult(allowed=False, audit=audit, problem=worm_problem)

        return PreflightResult(allowed=True, audit=audit, problem=None)

    def _validate_rbac(self, context: PreflightContext) -> Optional[ProblemDetail]:
        roles = set(context.roles)
        if not roles.intersection(self.config.allowed_roles):
            return ProblemDetail(
                status=HTTPStatus.FORBIDDEN,
                title="seed_preflight_forbidden",
                detail="RBAC minimo nao atendido para o comando seed_data.",
                type="https://iabank.local/problems/seed/preflight-forbidden",
            )

        if context.environment not in self.config.allowed_environments:
            return ProblemDetail(
                status=HTTPStatus.FORBIDDEN,
                title="seed_preflight_forbidden",
                detail="Ambiente nao autorizado para execucoes de seed_data.",
                type="https://iabank.local/problems/seed/preflight-forbidden",
            )

        return None

    def _validate_vault(self, audit: dict[str, object]) -> Optional[ProblemDetail]:
        vault_path = self.config.vault_transit_path
        audit["vault"]["available"] = bool(vault_path)
        if vault_path:
            audit["vault"]["path_fingerprint"] = self._fingerprint(vault_path)
            return None

        return ProblemDetail(
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            title="vault_unavailable",
            detail="Vault Transit indisponivel ou nao configurado.",
            type="https://iabank.local/problems/seed/vault-unavailable",
        )

    def _validate_worm(self, context: PreflightContext, audit: dict[str, object]) -> Optional[ProblemDetail]:
        worm_audit: dict[str, object] = audit["worm"]  # type: ignore[assignment]
        if context.dry_run and not self.config.enforce_worm_on_dry_run:
            worm_audit["skipped_for_dry_run"] = True
            worm_audit["available"] = False
            return None

        has_bucket = bool(self.config.worm_bucket)
        has_role = bool(self.config.worm_role_arn)
        has_kms = bool(self.config.worm_kms_key_id)

        worm_audit["available"] = has_bucket and has_role and has_kms
        worm_audit["skipped_for_dry_run"] = False

        if not worm_audit["available"]:
            return ProblemDetail(
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                title="WORM indisponivel",
                detail="Bucket/KMS/role do WORM nao configurados para seed_data.",
                type="https://iabank.local/problems/seed/worm-unavailable",
            )

        if self.config.worm_retention_days < self.min_worm_retention_days:
            return ProblemDetail(
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                title="WORM indisponivel",
                detail=(
                    f"Retencao WORM abaixo do minimo ({self.config.worm_retention_days}d < "
                    f"{self.min_worm_retention_days}d)."
                ),
                type="https://iabank.local/problems/seed/worm-unavailable",
            )

        worm_audit["retention_days"] = self.config.worm_retention_days
        worm_audit["bucket_fingerprint"] = self._fingerprint(self.config.worm_bucket)
        worm_audit["role_fingerprint"] = self._fingerprint(self.config.worm_role_arn)
        worm_audit["kms_fingerprint"] = self._fingerprint(self.config.worm_kms_key_id)
        return None

    def _build_audit(self, context: PreflightContext) -> dict[str, object]:
        return {
            "tenant_id": context.tenant_id,
            "environment": context.environment,
            "dry_run": context.dry_run,
            "roles": sorted(set(context.roles)),
            "requested_by": context.requested_by,
            "manifest_fingerprint": self._fingerprint(context.manifest_path),
            "vault": {"available": bool(self.config.vault_transit_path)},
            "worm": {
                "required": not context.dry_run or self.config.enforce_worm_on_dry_run,
                "available": bool(
                    self.config.worm_bucket and self.config.worm_role_arn and self.config.worm_kms_key_id,
                ),
                "retention_days": self.config.worm_retention_days,
            },
        }

    @staticmethod
    def _fingerprint(value: str) -> str:
        if not value:
            return ""
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
