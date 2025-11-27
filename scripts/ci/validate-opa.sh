#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
OPA_VERSION="${OPA_VERSION:-0.65.0}"
OPA_CACHE="${HOME}/.cache/opa/${OPA_VERSION}"
OPA_BIN="${OPA_CACHE}/opa"
PLAN_FIXTURE="${PLAN_FIXTURE:-${ROOT_DIR}/infra/opa/seed-data/fixtures/plan.json}"
TERRAFORM_DIR="${ROOT_DIR}/infra/terraform/seed-data"
PLAN_TMP_DIR=""
PLAN_OUT=""
PLAN_JSON_RAW=""
PLAN_JSON_WRAPPED=""

log() {
  printf '[validate-opa] %s\n' "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Erro: comando '$1' não encontrado. Instale antes de continuar."
    exit 1
  fi
}

ensure_opa() {
  if command -v opa >/dev/null 2>&1; then
    OPA_BIN="$(command -v opa)"
    return
  fi

  if [ ! -x "${OPA_BIN}" ]; then
    log "Baixando opa ${OPA_VERSION}..."
    mkdir -p "${OPA_CACHE}"
    curl -sSfL "https://openpolicyagent.org/downloads/v${OPA_VERSION}/opa_linux_amd64_static" -o "${OPA_BIN}"
    chmod +x "${OPA_BIN}"
  fi
}

cleanup() {
  if [ -n "${PLAN_TMP_DIR}" ] && [ -d "${PLAN_TMP_DIR}" ]; then
    rm -rf "${PLAN_TMP_DIR}"
  fi
}

run_terraform_checks() {
  log "terraform fmt -check (seed-data)"
  terraform -chdir="${TERRAFORM_DIR}" fmt -check

  log "terraform init -backend=false (seed-data)"
  terraform -chdir="${TERRAFORM_DIR}" init -backend=false -upgrade >/dev/null

  log "terraform validate (seed-data)"
  terraform -chdir="${TERRAFORM_DIR}" validate
}

generate_plan() {
  PLAN_TMP_DIR="$(mktemp -d)"
  PLAN_OUT="${PLAN_TMP_DIR}/plan.out"
  PLAN_JSON_RAW="${PLAN_TMP_DIR}/plan_raw.json"
  PLAN_JSON_WRAPPED="${PLAN_TMP_DIR}/plan_wrapped.json"

  TF_ENVIRONMENT="${TF_VAR_environment:-${environment:-staging}}"
  TF_TENANT="${TF_VAR_tenant_slug:-${tenant_slug:-tenant-a}}"
  TF_REDIS_AUTH="${TF_VAR_redis_auth_token:-dummy-token}"
  export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-dummy-access-key}"
  export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-dummy-secret}"
  export AWS_REGION="${AWS_REGION:-us-east-1}"
  export VAULT_TOKEN="${VAULT_TOKEN:-dummy-token}"

  log "terraform plan -refresh=false (seed-data)"
  if terraform -chdir="${TERRAFORM_DIR}" plan \
    -input=false \
    -refresh=false \
    -lock=false \
    -out="${PLAN_OUT}" \
    -var="environment=${TF_ENVIRONMENT}" \
    -var="tenant_slug=${TF_TENANT}" \
    -var="redis_auth_token=${TF_REDIS_AUTH}"; then
    log "terraform show -json (seed-data plan)"
    terraform -chdir="${TERRAFORM_DIR}" show -json "${PLAN_OUT}" >"${PLAN_JSON_RAW}"
  else
    log "Aviso: falha ao gerar plano Terraform; usando fixture ${PLAN_FIXTURE}"
    PLAN_JSON_RAW="${PLAN_FIXTURE}"
  fi

  log "Gerando wrapper de plano para OPA"
  python3 - "$PLAN_JSON_RAW" "$PLAN_FIXTURE" "$PLAN_JSON_WRAPPED" <<'PY'
import json, sys
plan_raw_path, fixture_path, out_path = sys.argv[1:4]

plan_data = {}
try:
    with open(plan_raw_path, "r", encoding="utf-8") as fh:
        plan_data = json.load(fh)
except Exception as exc:  # pragma: no cover
    sys.stderr.write(f"[validate-opa] Aviso: falha ao ler plano gerado: {exc}\n")

if isinstance(plan_data, dict) and "planned_values" not in plan_data and "seed_plan" in plan_data:
    plan_data = plan_data.get("seed_plan", {})

if not plan_data:
    with open(fixture_path, "r", encoding="utf-8") as fh:
        fixture = json.load(fh)
    plan_data = fixture.get("seed_plan", {})

with open(out_path, "w", encoding="utf-8") as fh:
    json.dump({"seed_plan_live": plan_data}, fh)
PY
}

run_opa_tests() {
  local input_file="${PLAN_JSON_WRAPPED:-${PLAN_FIXTURE}}"
  log "OPA tests (seed-data policies) [input=$(basename "${input_file}")]"
  "${OPA_BIN}" test \
    "${input_file}" \
    "${PLAN_FIXTURE}" \
    "${ROOT_DIR}/infra/opa/seed-data/policies" \
    "${ROOT_DIR}/infra/opa/seed-data/tests"
}

main() {
  require_cmd "curl"
  require_cmd "terraform"
  require_cmd "python3"

  ensure_opa
  trap cleanup EXIT
  run_terraform_checks

  generate_plan
  run_opa_tests
  log "OPA + Terraform OK"
}

main "$@"
