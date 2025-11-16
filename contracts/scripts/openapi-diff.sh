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

if ! command -v redocly >/dev/null 2>&1; then
  echo "Redocly CLI não encontrado no PATH. Instale com: pnpm add -D @redocly/cli" >&2
  exit 3
fi

echo "Comparando contratos (Redocly): $PREV_SPEC -> $CURR_SPEC"
redocly openapi diff "$PREV_SPEC" "$CURR_SPEC"
