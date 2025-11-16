#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PREV_SPEC="${1:-$ROOT_DIR/contracts/api.previous.yaml}"
CURR_SPEC="${2:-$ROOT_DIR/contracts/api.yaml}"

if [[ ! -f "$PREV_SPEC" ]]; then
  echo "Arquivo de baseline inexistente: $PREV_SPEC" >&2
  exit 2
fi

if [[ ! -f "$CURR_SPEC" ]]; then
  echo "Arquivo de contrato atual inexistente: $CURR_SPEC" >&2
  exit 2
fi

# Tenta com Redocly CLI (quando disponível com subcomando 'openapi diff').
if command -v redocly >/dev/null 2>&1; then
  echo "Comparando contratos (Redocly): $PREV_SPEC -> $CURR_SPEC"
  set +e
  redocly openapi diff "$PREV_SPEC" "$CURR_SPEC"
  rc=$?
  set -e
  if [ $rc -eq 0 ]; then
    exit 0
  fi
  echo "Aviso: 'redocly openapi diff' indisponível/não suportado nesta versão (rc=$rc). Tentando fallback 'oasdiff'..." >&2
else
  echo "Redocly CLI não encontrado no PATH. Tentando fallback 'oasdiff'." >&2
fi

# Fallback: tufin/oasdiff (suporta OpenAPI 3.1). Requer Docker.
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker não encontrado para fallback 'oasdiff'. Instale Docker ou ajuste a ferramenta de diff." >&2
  exit 4
fi

echo "Comparando contratos (oasdiff - breaking): $PREV_SPEC -> $CURR_SPEC"
docker run --rm -v "$(pwd)":"/work" -w /work tufin/oasdiff:latest \
  breaking -o ERR "$PREV_SPEC" "$CURR_SPEC"
