#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_DIR="${ROOT_DIR}/artifacts/seed-deps"
mkdir -p "${REPORT_DIR}"

echo "[seed-deps] Auditoria de dependências (seeds/factories/Vault/perf)."

if ! command -v poetry >/dev/null 2>&1; then
  echo "[seed-deps] Poetry não encontrado; instalando via pip para gerar requirements."
  python3 -m pip install --quiet poetry
fi

if [ -x "${ROOT_DIR}/scripts/security/run_python_sca.sh" ]; then
  echo "[seed-deps] Executando pip-audit (Poetry)."
  PYTHON_SCA_REPORT_DIR="${REPORT_DIR}/python" "${ROOT_DIR}/scripts/security/run_python_sca.sh" pip-audit
else
  echo "Script scripts/security/run_python_sca.sh não encontrado." >&2
  exit 1
fi

if command -v pnpm >/dev/null 2>&1; then
  echo "[seed-deps] Executando pnpm audit (critical, offline seeds tooling)."
  pnpm audit --prod --audit-level=critical --json > "${REPORT_DIR}/pnpm-audit.json"
else
  echo "pnpm não encontrado; necessário para auditar Spectral/Pact/k6 e ferramentas JS dos seeds." >&2
  exit 1
fi

echo "[seed-deps] Relatórios salvos em ${REPORT_DIR}."
