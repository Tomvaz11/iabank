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

if ! command -v oasdiff >/dev/null 2>&1; then
  echo "oasdiff não encontrado no PATH. Instale via Go: 'go install github.com/Tufin/oasdiff/cmd/oasdiff@v1.11.7' (ou use o CI)." >&2
  exit 3
fi

echo "Comparando contratos (breaking): $PREV_SPEC -> $CURR_SPEC"
oasdiff breaking "$PREV_SPEC" "$CURR_SPEC"
