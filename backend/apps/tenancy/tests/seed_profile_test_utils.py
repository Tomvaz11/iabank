from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Dict


BASELINE_CAPS = {
    'tenant_users': 5,
    'customers': 100,
    'addresses': 150,
    'consultants': 10,
    'bank_accounts': 120,
    'account_categories': 20,
    'suppliers': 30,
    'loans': 200,
    'installments': 2000,
    'financial_transactions': 4000,
    'limits': 100,
    'contracts': 150,
}

CARGA_CAPS = {
    'tenant_users': 10,
    'customers': 500,
    'addresses': 750,
    'consultants': 30,
    'bank_accounts': 600,
    'account_categories': 60,
    'suppliers': 150,
    'loans': 1000,
    'installments': 10000,
    'financial_transactions': 20000,
    'limits': 500,
    'contracts': 750,
}

DR_CAPS = dict(CARGA_CAPS)

ENVIRONMENT_MULTIPLIERS = {
    'dev': 1,
    'homolog': 3,
    'staging': 5,
    'perf': 5,
    'dr': 5,
    'prod': 1,
}


def _merge_dicts(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Realiza merge raso/recursivo de dicionários para permitir overrides em testes.
    """
    merged = deepcopy(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def compute_manifest_hash(manifest: Dict[str, Any]) -> str:
    """
    Calcula o hash do manifesto ignorando o campo manifest_hash para evitar ciclo.
    """
    payload = deepcopy(manifest)
    integrity = payload.get('integrity')
    if isinstance(integrity, dict) and 'manifest_hash' in integrity:
        integrity = {k: v for k, v in integrity.items() if k != 'manifest_hash'}
        payload['integrity'] = integrity

    serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def _volumetry_for(mode: str, environment: str) -> Dict[str, Dict[str, int]]:
    caps = BASELINE_CAPS
    if mode == 'carga':
        caps = CARGA_CAPS
    elif mode == 'dr':
        caps = DR_CAPS

    multiplier = ENVIRONMENT_MULTIPLIERS.get(environment, 1)
    return {entity: {'cap': int(value * multiplier)} for entity, value in caps.items()}


def build_manifest(
    tenant_slug: str,
    environment: str = 'staging',
    mode: str = 'baseline',
    overrides: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Monta um manifesto v1 mínimo válido e calcula o manifest_hash.
    """
    manifest: Dict[str, Any] = {
        'metadata': {
            'tenant': tenant_slug,
            'environment': environment,
            'profile': 'default',
            'version': '1.0.0',
            'schema_version': 'v1',
            'salt_version': 'v1',
        },
        'mode': mode,
        'reference_datetime': '2025-01-01T00:00:00Z',
        'window': {'start_utc': '00:00', 'end_utc': '06:00'},
        'volumetry': _volumetry_for(mode, environment),
        'rate_limit': {'limit': 120, 'window_seconds': 60},
        'backoff': {'base_seconds': 1, 'jitter_factor': 0.1, 'max_retries': 3, 'max_interval_seconds': 60},
        'budget': {'cost_cap_brl': 25.0, 'error_budget_pct': 10},
        'ttl': {'baseline_days': 1, 'carga_days': 2, 'dr_days': 2},
        'slo': {'p95_target_ms': 150, 'p99_target_ms': 250, 'throughput_target_rps': 1.5},
        'integrity': {'manifest_hash': ''},
    }

    if mode in {'carga', 'dr'}:
        manifest['integrity']['worm_proof'] = 'stub-worm-evidence'
        manifest['budget']['cost_model_version'] = '2025-01-15'

    if overrides:
        manifest = _merge_dicts(manifest, overrides)

    manifest['integrity']['manifest_hash'] = compute_manifest_hash(manifest)
    return manifest
