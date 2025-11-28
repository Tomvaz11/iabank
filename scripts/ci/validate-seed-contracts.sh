#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACT_STUBS=(
  "$ROOT_DIR/contracts/pacts/financial-calculator.json"
  "$ROOT_DIR/contracts/pacts/seed-data-outbound-block.json"
)

"$ROOT_DIR/scripts/ci/seed-data-lint.sh"

for stub in "${PACT_STUBS[@]}"; do
  if [ -f "$stub" ]; then
    printf "[seed-data] Validando stub Pact %s...\n" "$(basename "$stub")"
    node -e "JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))" "$stub"
  else
    echo "Stub Pact ausente em $stub" >&2
    exit 1
  fi
done

printf "[seed-data] Stubs Pact prontos para Prism/offline (integrações externas bloqueadas).\n"
