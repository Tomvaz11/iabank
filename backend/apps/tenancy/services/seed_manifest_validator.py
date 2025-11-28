from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID

from django.utils import timezone
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parents[4] / 'contracts' / 'seed-profile.schema.json'


def compute_manifest_hash(manifest: Dict[str, Any] | None) -> str:
    if not isinstance(manifest, dict):
        return ''

    payload = copy.deepcopy(manifest)
    integrity = payload.get('integrity')
    if isinstance(integrity, dict) and 'manifest_hash' in integrity:
        integrity = {k: v for k, v in integrity.items() if k != 'manifest_hash'}
        payload['integrity'] = integrity

    serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


@dataclass
class ValidationResult:
    valid: bool
    issues: list[str]
    violations: list[dict[str, str]]
    manifest_hash: str
    normalized_version: Optional[str] = None


@dataclass
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_at: datetime
    retry_after: int


@dataclass
class _RateLimitState:
    limit: int
    remaining: int
    reset_at: datetime


class SimpleRateLimiter:
    def __init__(self) -> None:
        self._state: dict[tuple[str, str], _RateLimitState] = {}

    def check(self, *, tenant_id: UUID, environment: str, limit: int, window_seconds: int) -> RateLimitDecision:
        now = timezone.now()
        window_delta = timedelta(seconds=max(1, window_seconds))
        normalized_limit = max(1, limit)
        key = (str(tenant_id), environment)
        state = self._state.get(key)

        if state is None or state.reset_at <= now:
            state = _RateLimitState(limit=normalized_limit, remaining=normalized_limit, reset_at=now + window_delta)

        if state.remaining <= 0:
            retry_after = max(1, int((state.reset_at - now).total_seconds()))
            self._state[key] = state
            return RateLimitDecision(
                allowed=False,
                limit=state.limit,
                remaining=0,
                reset_at=state.reset_at,
                retry_after=retry_after,
            )

        state.remaining -= 1
        retry_after = max(1, int((state.reset_at - now).total_seconds()))
        self._state[key] = state
        return RateLimitDecision(
            allowed=True,
            limit=state.limit,
            remaining=state.remaining,
            reset_at=state.reset_at,
            retry_after=retry_after,
        )


class SeedManifestValidator:
    def __init__(self, schema_path: Path | None = None) -> None:
        self.schema_path = schema_path or DEFAULT_SCHEMA_PATH
        self._validator: Draft202012Validator | None = None

    def validate_manifest(self, manifest: Dict[str, Any] | None, *, environment: str | None = None) -> ValidationResult:
        manifest_hash = compute_manifest_hash(manifest)
        if not isinstance(manifest, dict):
            violation = {
                'field': 'manifest',
                'message': 'Manifesto deve ser um objeto JSON válido.',
                'code': 'invalid_type',
            }
            return ValidationResult(False, [violation['message']], [violation], manifest_hash)

        validator = self._get_validator()
        errors = sorted(validator.iter_errors(manifest), key=lambda err: err.json_path)
        violations: list[dict[str, str]] = [
            {
                'field': '.'.join([str(part) for part in error.path]) or error.json_path.lstrip('$.'),
                'message': error.message,
                'code': str(error.validator),
            }
            for error in errors
        ]

        integrity = manifest.get('integrity') if isinstance(manifest, dict) else None
        integrity_hash = integrity.get('manifest_hash') if isinstance(integrity, dict) else None
        if integrity_hash and integrity_hash != manifest_hash:
            violations.append(
                {
                    'field': 'integrity.manifest_hash',
                    'message': 'Hash do manifesto não confere com o payload informado.',
                    'code': 'manifest_hash_mismatch',
                }
            )

        if environment and manifest.get('metadata', {}).get('environment') != environment:
            violations.append(
                {
                    'field': 'metadata.environment',
                    'message': 'Cabeçalho X-Environment diverge do manifesto.',
                    'code': 'environment_mismatch',
                }
            )

        issues = [violation['message'] for violation in violations]
        return ValidationResult(
            valid=not violations,
            issues=issues,
            violations=violations,
            manifest_hash=manifest_hash,
            normalized_version=manifest.get('metadata', {}).get('version'),
        )

    @staticmethod
    def extract_caps(manifest: Dict[str, Any] | None) -> Dict[str, int]:
        volumetry = manifest.get('volumetry') if isinstance(manifest, dict) else None
        if not isinstance(volumetry, dict):
            return {}

        caps: dict[str, int] = {}
        for entity, config in volumetry.items():
            if not isinstance(config, dict):
                continue
            cap = config.get('cap')
            try:
                caps[entity] = int(cap)
            except (TypeError, ValueError):
                continue
        return caps

    @staticmethod
    def extract_rate_limit(manifest: Dict[str, Any] | None) -> tuple[int, int]:
        rate_limit = manifest.get('rate_limit') if isinstance(manifest, dict) else None
        limit = 1
        window_seconds = 60
        if isinstance(rate_limit, dict):
            try:
                limit = int(rate_limit.get('limit', limit))
            except (TypeError, ValueError):
                limit = 1
            try:
                window_seconds = int(rate_limit.get('window_seconds', window_seconds))
            except (TypeError, ValueError):
                window_seconds = 60
        return max(1, limit), max(1, window_seconds)

    def _get_validator(self) -> Draft202012Validator:
        if self._validator is None:
            schema = self._load_schema()
            self._validator = Draft202012Validator(schema, format_checker=FormatChecker())
        return self._validator

    def _load_schema(self) -> Dict[str, Any]:
        try:
            with self.schema_path.open('r', encoding='utf-8') as handle:
                return json.load(handle)
        except OSError as exc:  # pragma: no cover - falha operacional
            raise RuntimeError(f'Não foi possível carregar o schema em {self.schema_path}') from exc
        except SchemaError as exc:  # pragma: no cover - schema inválido impede execução
            raise RuntimeError(f'Schema inválido em {self.schema_path}') from exc
