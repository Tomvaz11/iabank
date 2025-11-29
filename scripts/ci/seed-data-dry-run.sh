#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_MANIFEST="$ROOT_DIR/configs/seed_profiles/staging/tenant-a.yaml"
MANIFEST_PATH="${SEED_PROFILE_PATH:-$DEFAULT_MANIFEST}"
TENANT_ID="${SEED_TENANT_ID:-00000000-0000-0000-0000-000000000001}"
ENVIRONMENT="${SEED_ENVIRONMENT:-staging}"
MODE="${SEED_MODE:-baseline}"
IDEMPOTENCY_KEY="${IDEMPOTENCY_KEY:-seed-dry-run-$(uuidgen 2>/dev/null || date +%s)}"
REFERENCE_DATETIME="${SEED_REFERENCE_DATETIME:-}" # opcional
REQUESTED_BY="${SEED_REQUESTED_BY:-seed-ci}"

if [ ! -f "$MANIFEST_PATH" ]; then
  echo "Manifesto não encontrado em $MANIFEST_PATH" >&2
  exit 1
fi

if [ -n "$REFERENCE_DATETIME" ]; then
  REF_ARGS=(--reference-datetime "$REFERENCE_DATETIME")
else
  REF_ARGS=()
fi

CMD_BASE=(
  poetry run python "$ROOT_DIR/backend/manage.py" seed_data
  --tenant-id "$TENANT_ID"
  --environment "$ENVIRONMENT"
  --manifest-path "$MANIFEST_PATH"
  --mode "$MODE"
  --idempotency-key "$IDEMPOTENCY_KEY"
  --requested-by "$REQUESTED_BY"
  --dry-run
)
CMD=("${CMD_BASE[@]}" "${REF_ARGS[@]}")

if [ "${SIMULATE_TELEMETRY_FAILURE:-0}" = "1" ]; then
  echo "[seed-data] Simulação de falha OTEL/Sentry requisitada; retornando exit 4."
  exit 4
fi

MISSING_ENV=()
for var in VAULT_TRANSIT_PATH SEEDS_WORM_BUCKET SEEDS_WORM_ROLE_ARN SEEDS_WORM_KMS_KEY_ID SEEDS_WORM_RETENTION_DAYS; do
  if [ -z "${!var:-}" ]; then
    MISSING_ENV+=("$var")
  fi
done

if [ "${#MISSING_ENV[@]}" -gt 0 ]; then
  echo "[seed-data] Variáveis ausentes (${MISSING_ENV[*]}). Usando stub seguro (sem Vault/WORM)."
elif command -v poetry >/dev/null 2>&1 && [ -f "$ROOT_DIR/backend/manage.py" ]; then
  if poetry run python "$ROOT_DIR/backend/manage.py" help seed_data >/dev/null 2>&1; then
    echo "[seed-data] Executando dry-run real (fail-close em OTEL/Sentry)."
    "${CMD[@]}"
  else
    echo "[seed-data] Comando seed_data ainda não disponível; usando stub seguro (sem WORM/checkpoints)."
  fi
else
  echo "[seed-data] Ambiente Python/poetry indisponível; stub aplicado (sem executar comando)."
fi

echo "[seed-data] Dry-run concluído com Idempotency-Key=$IDEMPOTENCY_KEY e manifesto $MANIFEST_PATH"
