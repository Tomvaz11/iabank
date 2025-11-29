#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONTRACT_PATH="$ROOT_DIR/contracts/seed-data.openapi.yaml"
SPEC_CONTRACT_PATH="$ROOT_DIR/specs/003-seed-data-automation/contracts/seed-data.openapi.yaml"
SCHEMA_PATH="$ROOT_DIR/contracts/seed-profile.schema.json"
VALIDATOR_SCRIPT="$ROOT_DIR/scripts/ci/seed-manifest-validate.js"

if ! command -v pnpm >/dev/null 2>&1; then
  echo "pnpm não encontrado; instale para rodar lint dos contratos." >&2
  exit 1
fi

if [ ! -f "$CONTRACT_PATH" ] || [ ! -f "$SPEC_CONTRACT_PATH" ]; then
  echo "Contrato seed-data ausente; verifique paths em $CONTRACT_PATH e $SPEC_CONTRACT_PATH." >&2
  exit 1
fi

printf "[seed-data] Spectral lint...\n"
pnpm exec spectral lint --ruleset="$ROOT_DIR/contracts/.spectral.yaml" \
  "$CONTRACT_PATH" "$SPEC_CONTRACT_PATH"

printf "[seed-data] oasdiff (breaking) spec -> repo...\n"
if command -v oasdiff >/dev/null 2>&1; then
  oasdiff breaking "$SPEC_CONTRACT_PATH" "$CONTRACT_PATH"
else
  echo "oasdiff não encontrado no PATH (instale v1.11.7 ou execute via CI)." >&2
  exit 1
fi

printf "[seed-data] Validando schema JSON...\n"
node -e "JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))" "$SCHEMA_PATH"

printf "[seed-data] Validando manifestos e caps Q11...\n"
node "$VALIDATOR_SCRIPT" --schema "$SCHEMA_PATH" --root "$ROOT_DIR"

printf "[seed-data] Lint/diff concluído.\n"
