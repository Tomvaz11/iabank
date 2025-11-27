#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACT_STUB="$ROOT_DIR/contracts/pacts/financial-calculator.json"

"$ROOT_DIR/scripts/ci/seed-data-lint.sh"

if [ -f "$PACT_STUB" ]; then
  printf "[seed-data] Validando stub Pact financial-calculator...\n"
  node -e "JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))" "$PACT_STUB"
else
  echo "Stub Pact ausente em $PACT_STUB" >&2
  exit 1
fi
