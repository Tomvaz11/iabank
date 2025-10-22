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

if ! command -v openapi-diff >/dev/null 2>&1; then
  echo "openapi-diff não encontrado no PATH. Instale com pnpm add -D openapi-diff." >&2
  exit 3
fi

echo "Comparando contratos: $PREV_SPEC -> $CURR_SPEC"
openapi-diff "$PREV_SPEC" "$CURR_SPEC"
