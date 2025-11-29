#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACT_STUBS=(
  "$ROOT_DIR/contracts/pacts/financial-calculator.json"
  "$ROOT_DIR/contracts/pacts/seed-data-outbound-block.json"
  "$ROOT_DIR/contracts/pacts/kyc.json"
  "$ROOT_DIR/contracts/pacts/pagamentos.json"
  "$ROOT_DIR/contracts/pacts/notificacoes.json"
)
CHECKLIST_FILE="$ROOT_DIR/observabilidade/checklists/seed-worm-checklist.json"

"$ROOT_DIR/scripts/ci/seed-data-lint.sh"

if [ -f "$CHECKLIST_FILE" ]; then
  printf "[seed-data] Validando checklist WORM em %s...\n" "$CHECKLIST_FILE"
  node - "$CHECKLIST_FILE" <<'NODE'
    const fs = require('fs');
    const path = process.argv[2];
    const raw = fs.readFileSync(path, 'utf8');
    const data = JSON.parse(raw);
    const items = Array.isArray(data.items) ? data.items : [];
    const ids = new Set(items.map((item) => item.id));
    const required = [
      'pii_masked',
      'rls_enforced',
      'contracts_aligned',
      'idempotency_reused',
      'rate_limit_respected',
      'slo_met',
    ];
    const missing = required.filter((id) => !ids.has(id));
    if (missing.length) {
      throw new Error(`Checklist WORM faltando itens obrigatórios: ${missing.join(', ')}`);
    }
NODE
else
  echo "Checklist WORM ausente em $CHECKLIST_FILE" >&2
  exit 1
fi

validate_stub_contract() {
  local stub_path="$1"
  node - "$stub_path" <<'NODE'
    const fs = require('fs');
    const path = process.argv[2];
    const data = JSON.parse(fs.readFileSync(path, 'utf8'));
    const interactions = Array.isArray(data.interactions) ? data.interactions : [];
    const statuses = interactions.map((item) => Number((item.response || {}).status || 0));
    const has2xx = statuses.some((code) => code >= 200 && code < 300);
    const has429 = statuses.includes(429);
    const isFinancial = path.includes('financial-calculator.json');
    const isOutboundBlock = path.includes('seed-data-outbound-block.json');
    if (isOutboundBlock) {
      process.exit(0);
    }
    if (!has2xx || (!has429 && !isFinancial)) {
      throw new Error(`Stub ${path} precisa de respostas 2xx e 429 para rate-limit/backoff.`);
    }
NODE
}

for stub in "${PACT_STUBS[@]}"; do
  if [ -f "$stub" ]; then
    printf "[seed-data] Validando stub Pact %s...\n" "$(basename "$stub")"
    node -e "JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))" "$stub"
    validate_stub_contract "$stub"
  else
    echo "Stub Pact ausente em $stub" >&2
    exit 1
  fi
done

printf "[seed-data] Stubs Pact prontos para Prism/offline (integrações externas bloqueadas).\n"
