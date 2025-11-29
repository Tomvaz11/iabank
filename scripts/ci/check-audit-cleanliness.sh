#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

usage() {
  cat <<'USAGE'
Valida limpeza de logs/WORM de seed_data (labels obrigatórias e ausência de PII).
Uso:
  scripts/ci/check-audit-cleanliness.sh [--logs <paths>] [--worm <paths>]

Parâmetros:
  --logs  Lista separada por vírgula com arquivos de log JSONL (default: observabilidade/data/seed-audit.log.jsonl)
  --worm  Lista separada por vírgula com relatórios WORM (default: observabilidade/data/seed-worm-report.sample.json)
USAGE
}

LOG_PATHS=""
WORM_PATHS=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --logs)
      LOG_PATHS="$2"
      shift 2
      ;;
    --worm)
      WORM_PATHS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Parâmetro desconhecido: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$LOG_PATHS" ]]; then
  LOG_PATHS="$ROOT_DIR/observabilidade/data/seed-audit.log.jsonl"
fi

if [[ -z "$WORM_PATHS" ]]; then
  WORM_PATHS="$ROOT_DIR/observabilidade/data/seed-worm-report.sample.json"
fi

export LOG_PATHS
export WORM_PATHS

python3 - <<'PY'
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence

log_paths = [Path(p) for p in os.environ.get("LOG_PATHS", "").split(",") if p.strip()]
w_paths = [Path(p) for p in os.environ.get("WORM_PATHS", "").split(",") if p.strip()]

errors: list[str] = []
required_labels = ("tenant_id", "environment", "seed_run_id", "manifest_version", "mode")
sensitive_patterns: Sequence[re.Pattern[str]] = (
    re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),  # CPF
    re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),  # CNPJ
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b\+?\d{2}\s?\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b"),
)
mask_tokens = ("[Filtered]", "[FILTERED]", "[REDACTED]", "*****")
uuid_pattern = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _read_jsonl(path: Path) -> Iterable[dict]:
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                yield json.loads(raw)
            except json.JSONDecodeError as exc:
                errors.append(f"{path}:{line_no} JSON inválido: {exc}")


def _has_pii(value: object) -> bool:
    if not isinstance(value, str):
        return False
    if any(token.lower() in value.lower() for token in mask_tokens):
        return False
    if uuid_pattern.match(value):
        return False
    return any(pattern.search(value) for pattern in sensitive_patterns)


def _check_labels(payload: dict, *, path: Path, prefix: str) -> None:
    missing = [label for label in required_labels if not payload.get(label)]
    if missing:
        errors.append(f"{prefix} {path} sem labels obrigatórias: {', '.join(missing)}")


def _check_log_entry(entry: dict, *, path: Path) -> None:
    _check_labels(entry, path=path, prefix="Log")
    if entry.get("pii_redacted") is False:
        errors.append(f"Log {path} marca pii_redacted=false")
    for key, value in entry.items():
        if _has_pii(value):
            errors.append(f"PII potencial em {path}: chave '{key}' valor='{value}'")


def _check_worm(payload: dict, *, path: Path) -> None:
    _check_labels(payload, path=path, prefix="WORM")
    trace = payload.get("trace") or {}
    if not trace.get("trace_id") or not trace.get("span_id"):
        errors.append(f"WORM {path} sem trace_id/span_id")
    checklist = payload.get("checklist") or {}
    summary = checklist.get("summary") or {}
    if summary.get("failed"):
        errors.append(f"WORM {path} com checklist reprovado: {summary.get('failed_ids')}")
    for key, value in payload.items():
        if _has_pii(value):
            errors.append(f"PII potencial em WORM {path}: chave '{key}' valor='{value}'")


def _require_files(paths: Sequence[Path], kind: str) -> Sequence[Path]:
    existing = [p for p in paths if p.exists()]
    if not existing:
        errors.append(f"Nenhum arquivo encontrado para {kind}: {', '.join(str(p) for p in paths)}")
    return existing


log_paths = _require_files(log_paths, "logs")
w_paths = _require_files(w_paths, "WORM")

for path in log_paths:
    for entry in _read_jsonl(path):
        if isinstance(entry, dict):
            _check_log_entry(entry, path=path)

for path in w_paths:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - erros de IO/JSON são reportados abaixo
        errors.append(f"Falha ao ler WORM {path}: {exc}")
        continue
    if isinstance(payload, dict):
        _check_worm(payload, path=path)
    else:
        errors.append(f"WORM {path} não é um objeto JSON")

if errors:
    for err in errors:
        print(f"✗ {err}", file=sys.stderr)
    sys.exit(1)

print("✓ Logs/WORM de seed_data limpos e rotulados")
PY
