#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SEMGREP_CONFIG="${ROOT_DIR}/scripts/security/semgrep.yml"

if [[ ! -f "${SEMGREP_CONFIG}" ]]; then
  echo "Configuração do Semgrep não encontrada em ${SEMGREP_CONFIG}." >&2
  exit 1
fi

if command -v poetry >/dev/null 2>&1; then
  SEMGREP_CMD=("poetry" "run" "semgrep")
elif command -v semgrep >/dev/null 2>&1; then
  SEMGREP_CMD=("semgrep")
else
  echo "Semgrep não encontrado; instalando via pip..." >&2
  python -m pip install --quiet "semgrep==1.94.0"
  SEMGREP_CMD=("semgrep")
fi

CI_REF="${GITHUB_REF:-}"
if [[ "${CI_RELEASE:-false}" == "true" ]] || [[ "${CI_ENFORCE_FULL_SECURITY:-false}" == "true" ]] || [[ "${GITHUB_REF_TYPE:-}" == "tag" ]] || [[ "${CI_REF}" == refs/heads/main ]] || [[ "${CI_REF}" == refs/heads/release/* ]]; then
  MIN_SEVERITY="WARNING"
  echo "Executando Semgrep em modo fail-closed (threshold WARNING)."
else
  MIN_SEVERITY="${SEMGRP_MIN_SEVERITY:-ERROR}"
  echo "Executando Semgrep com threshold ${MIN_SEVERITY}."
fi

TARGETS=(
  "${ROOT_DIR}/backend"
  "${ROOT_DIR}/frontend"
  "${ROOT_DIR}/scripts"
)

export SEMGREP_ENABLE_VERSION_CHECK=0

"${SEMGREP_CMD[@]}" scan \
  --config "${SEMGREP_CONFIG}" \
  --severity "${MIN_SEVERITY}" \
  --error \
  --metrics=off \
  --disable-version-check \
  --timeout 0 \
  "${TARGETS[@]}"
