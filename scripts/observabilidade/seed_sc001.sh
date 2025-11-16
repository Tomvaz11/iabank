#!/usr/bin/env bash
set -euo pipefail

# Seed simples para gerar eventos SC-001 e facilitar visualização local
# Uso: scripts/observabilidade/seed_sc001.sh [FEATURE_SLUG] [N]
# Vars: BACKEND_URL (default http://127.0.0.1:58000), TENANT_ID (seed padrão)

BACKEND_URL=${BACKEND_URL:-http://127.0.0.1:58000}
TENANT_ID=${TENANT_ID:-00000000-0000-0000-0000-000000000001}
FEATURE=${1:-loan-tracking-local}
COUNT=${2:-1}

echo "[seed] Backend: ${BACKEND_URL} | Tenant: ${TENANT_ID} | Feature: ${FEATURE} | Count: ${COUNT}"

for i in $(seq 1 "${COUNT}"); do
  KEY=$(python3 - <<'PY'
import uuid; print(uuid.uuid4())
PY
)
  echo "[seed] POST ${i}/${COUNT} -> features/scaffold …"
  curl -s -X POST "${BACKEND_URL}/api/v1/tenants/${TENANT_ID}/features/scaffold" \
    -H 'Content-Type: application/json' \
    -H "X-Tenant-Id: ${TENANT_ID}" \
    -H "Idempotency-Key: ${KEY}" \
    -d @- <<JSON | sed -n '1,1p' >/dev/null
{
  "featureSlug": "${FEATURE}",
  "initiatedBy": "00000000-0000-4000-8000-000000000123",
  "slices": [
    { "slice": "app",   "files": [{"path":"frontend/src/app/${FEATURE}/index.tsx",   "checksum": "4a7d1ed414474e4033ac29ccb8653d9b4a7d1ed414474e4033ac29ccb8653d9b"}]},
    { "slice": "pages", "files": [{"path":"frontend/src/pages/${FEATURE}/index.tsx", "checksum": "6b86b273ff34fce19d6b804eff5a3f5746e0f2c6313be24d09aef7b54afc8cdd"}]}
  ],
  "lintCommitHash": "1234567890abcdef1234567890abcdef12345678",
  "scReferences": ["@SC-001", "@SC-003"],
  "durationMs": 1450,
  "metadata": {"cliVersion": "0.1.0"}
}
JSON
done

echo "[seed] Métricas SC-001 publicadas. Dica: use o dashboard 'IABank Foundation — Observabilidade Local (Demo)'"

