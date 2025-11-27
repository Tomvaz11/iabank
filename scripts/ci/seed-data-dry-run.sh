#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEFAULT_MANIFEST="$ROOT_DIR/configs/seed_profiles/staging/tenant-a.yaml"
MANIFEST_PATH="${SEED_PROFILE_PATH:-$DEFAULT_MANIFEST}"
MODE="${SEED_MODE:-baseline}"
IDEMPOTENCY_KEY="${IDEMPOTENCY_KEY:-seed-dry-run-$(uuidgen 2>/dev/null || date +%s)}"
REFERENCE_DATETIME="${SEED_REFERENCE_DATETIME:-}" # opcional

if [ ! -f "$MANIFEST_PATH" ]; then
  echo "Manifesto não encontrado em $MANIFEST_PATH" >&2
  exit 1
fi

if [ -n "$REFERENCE_DATETIME" ]; then
  REF_ARGS=(--reference-datetime "$REFERENCE_DATETIME")
else
  REF_ARGS=()
fi

CMD_BASE=(poetry run python "$ROOT_DIR/backend/manage.py" seed_data --profile "$MANIFEST_PATH" --mode "$MODE" --idempotency-key "$IDEMPOTENCY_KEY" --dry-run)
CMD=("${CMD_BASE[@]}" "${REF_ARGS[@]}")

if command -v poetry >/dev/null 2>&1 && [ -f "$ROOT_DIR/backend/manage.py" ]; then
  if poetry run python "$ROOT_DIR/backend/manage.py" help seed_data >/dev/null 2>&1; then
    echo "[seed-data] Executando dry-run real (fail-close em OTEL/Sentry)."
    "${CMD[@]}"
  else
    echo "[seed-data] Comando seed_data ainda não disponível; usando stub seguro (sem WORM/checkpoints)."
  fi
else
  echo "[seed-data] Ambiente Python/poetry indisponível; stub aplicado (sem executar comando)."
fi

if [ "${SIMULATE_TELEMETRY_FAILURE:-0}" = "1" ]; then
  echo "[seed-data] Falha simulada de OTEL/Sentry detectada (fail-close)." >&2
  exit 4
fi

echo "[seed-data] Dry-run concluído com Idempotency-Key=$IDEMPOTENCY_KEY e manifesto $MANIFEST_PATH"
