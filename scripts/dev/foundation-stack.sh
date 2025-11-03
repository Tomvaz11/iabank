#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

COMPOSE_FILE="${FOUNDATION_STACK_COMPOSE:-${REPO_ROOT}/infra/docker-compose.foundation.yml}"
PROJECT_NAME="${FOUNDATION_STACK_PROJECT:-foundation}"

NATIVE_STATE_DIR="${FOUNDATION_STACK_STATE_DIR:-${REPO_ROOT}/artifacts/foundation-stack}"
NATIVE_PID_FILE="${NATIVE_STATE_DIR}/backend.pid"
NATIVE_LOG_FILE="${NATIVE_STATE_DIR}/backend.log"

detect_mode() {
  if [[ "${FOUNDATION_STACK_MODE:-}" == "native" ]]; then
    echo "native"
    return
  fi

  if command -v docker >/dev/null 2>&1; then
    echo "docker"
    return
  fi

  echo "native"
}

STACK_MODE="$(detect_mode)"

usage() {
  cat <<'EOF'
Uso: foundation-stack.sh <comando> [opções]

Comandos:
  up [serviços...]       Sobe a stack (docker ou modo nativo quando docker estiver ausente)
  down                   Derruba stack e remove containers/processos
  ps                     Lista status dos serviços/processos
  logs [serviço]         Exibe logs (segue se nenhum serviço for especificado)
  seed                   Executa seed manual dos tenants/tokens (via manage.py)

Variáveis de ambiente úteis:
  FOUNDATION_STACK_COMPOSE   Caminho alternativo do docker-compose (default: infra/docker-compose.foundation.yml)
  FOUNDATION_STACK_PROJECT   Nome do projeto docker compose (default: foundation)
  FOUNDATION_STACK_MODE      Força modo 'docker' ou 'native' (por padrão detecta automaticamente)
  FOUNDATION_STACK_STATE_DIR Diretório para logs/PIDs no modo nativo (default: artifacts/foundation-stack)

Exemplos:
  ./scripts/dev/foundation-stack.sh up
  ./scripts/dev/foundation-stack.sh logs backend
EOF
}

ensure_docker() {
  if [[ "${STACK_MODE}" != "docker" ]]; then
    return
  fi

  if ! command -v docker >/dev/null 2>&1; then
    cat <<'EOF' >&2
erro: docker não encontrado no PATH.
Sugestão (Ubuntu/WSL2):
  sudo apt-get install ca-certificates curl gnupg lsb-release
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$UBUNTU_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update
  sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER" && newgrp docker

Após instalar, rode novamente este script.
EOF
    exit 1
  fi
}

ensure_poetry() {
  if ! command -v poetry >/dev/null 2>&1; then
    cat <<'EOF' >&2
erro: poetry não encontrado no PATH.
Instale o Poetry conforme https://python-poetry.org/docs/#installation e tente novamente.
EOF
    exit 1
  fi
}

docker_compose() {
  docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" "$@"
}

native_env() {
  export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-backend.config.settings}"
  export FOUNDATION_DB_VENDOR="postgresql"
  export FOUNDATION_DB_HOST="${FOUNDATION_DB_HOST:-127.0.0.1}"
  export FOUNDATION_DB_PORT="${FOUNDATION_DB_PORT:-5432}"
  export FOUNDATION_DB_NAME="${FOUNDATION_DB_NAME:-foundation}"
  export FOUNDATION_DB_USER="${FOUNDATION_DB_USER:-foundation}"
  export FOUNDATION_DB_PASSWORD="${FOUNDATION_DB_PASSWORD:-foundation}"
  export FOUNDATION_DB_CONN_MAX_AGE="${FOUNDATION_DB_CONN_MAX_AGE:-0}"
  unset FOUNDATION_SQLITE_PATH
  export FOUNDATION_PGCRYPTO_KEY="${FOUNDATION_PGCRYPTO_KEY:-dev-only-pgcrypto-key}"
  export FOUNDATION_TELEMETRY_DISABLED="${FOUNDATION_TELEMETRY_DISABLED:-true}"
  export OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://127.0.0.1:4318}"
  export VITE_OTEL_EXPORTER_OTLP_ENDPOINT="${VITE_OTEL_EXPORTER_OTLP_ENDPOINT:-http://127.0.0.1:4318}"
  export FOUNDATION_STACK_BACKEND_PORT="${FOUNDATION_STACK_BACKEND_PORT:-8000}"
}

native_status() {
  if [[ -f "${NATIVE_PID_FILE}" ]]; then
    local pid
    pid="$(cat "${NATIVE_PID_FILE}")"
    if ps -p "${pid}" >/dev/null 2>&1; then
      echo "ativo (pid=${pid})"
      return 0
    fi
  fi
  echo "inativo"
  return 1
}

native_up() {
  ensure_poetry
  native_env

  mkdir -p "${NATIVE_STATE_DIR}"

  if [[ -f "${NATIVE_PID_FILE}" ]]; then
    local pid
    pid="$(cat "${NATIVE_PID_FILE}")"
    if ps -p "${pid}" >/dev/null 2>&1; then
      echo "Stack nativa já está em execução (pid=${pid}). Use 'down' para reiniciar." >&2
      exit 0
    fi
  fi

  echo "[foundation-stack:native] Executando migrations (PostgreSQL em ${FOUNDATION_DB_HOST}:${FOUNDATION_DB_PORT}/${FOUNDATION_DB_NAME})"
  poetry run python backend/manage.py migrate --noinput
  echo "[foundation-stack:native] Populando tenants padrão"
  if ! poetry run python backend/manage.py seed_foundation_tenants --force; then
    echo "[foundation-stack:native] Aviso: seed de tenants falhou. Verifique acesso ao banco PostgreSQL configurado." >&2
  fi

  local port="${FOUNDATION_STACK_BACKEND_PORT}"
  echo "[foundation-stack:native] Iniciando backend Django em http://127.0.0.1:${port}"
  (
    cd "${REPO_ROOT}"
    POETRY_HOME="${POETRY_HOME:-$HOME/.poetry}" \
      FOUNDATION_DB_VENDOR="${FOUNDATION_DB_VENDOR}" \
      FOUNDATION_PGCRYPTO_KEY="${FOUNDATION_PGCRYPTO_KEY}" \
      FOUNDATION_DB_HOST="${FOUNDATION_DB_HOST}" \
      FOUNDATION_DB_PORT="${FOUNDATION_DB_PORT}" \
      FOUNDATION_DB_NAME="${FOUNDATION_DB_NAME}" \
      FOUNDATION_DB_USER="${FOUNDATION_DB_USER}" \
      FOUNDATION_DB_PASSWORD="${FOUNDATION_DB_PASSWORD}" \
      FOUNDATION_STACK_BACKEND_PORT="${FOUNDATION_STACK_BACKEND_PORT}" \
      FOUNDATION_STACK_STATE_DIR="${NATIVE_STATE_DIR}" \
      DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}" \
      poetry run python backend/manage.py runserver "0.0.0.0:${port}"
  ) >>"${NATIVE_LOG_FILE}" 2>&1 &

  local pid=$!
  echo "${pid}" >"${NATIVE_PID_FILE}"

  echo "[foundation-stack:native] Backend rodando (pid=${pid}). Logs em ${NATIVE_LOG_FILE}"
  echo "[foundation-stack:native] Finalize com Ctrl+C ou './scripts/dev/foundation-stack.sh down'"
}

native_down() {
  native_env
  if [[ ! -f "${NATIVE_PID_FILE}" ]]; then
    echo "Stack nativa não está em execução."
    return
  fi

  local pid
  pid="$(cat "${NATIVE_PID_FILE}")"
  if ps -p "${pid}" >/dev/null 2>&1; then
    echo "[foundation-stack:native] Encerrando processo ${pid}"
    kill "${pid}" >/dev/null 2>&1 || true
    wait "${pid}" 2>/dev/null || true
  else
    echo "[foundation-stack:native] PID ${pid} não está ativo."
  fi

  rm -f "${NATIVE_PID_FILE}"
  echo "[foundation-stack:native] Encerrado."
}

native_ps() {
  native_env
  printf "%-10s %-8s %-s\n" "SERVIÇO" "STATUS" "DETALHES"
  if native_status >/dev/null; then
    local pid
    pid="$(cat "${NATIVE_PID_FILE}")"
    printf "%-10s %-8s %-s\n" "backend" "ativo" "pid=${pid} porta=${FOUNDATION_STACK_BACKEND_PORT}"
  else
    printf "%-10s %-8s %-s\n" "backend" "inativo" "-"
  fi
}

native_logs() {
  native_env
  if [[ ! -f "${NATIVE_LOG_FILE}" ]]; then
    echo "Nenhum log disponível ainda (arquivo ${NATIVE_LOG_FILE} inexistente)."
    return
  fi

  tail -f "${NATIVE_LOG_FILE}"
}

native_seed() {
  ensure_poetry
  native_env
  poetry run python backend/manage.py seed_foundation_tenants --force
}

run_up() {
  if [[ "${STACK_MODE}" == "docker" ]]; then
    docker_compose up -d "$@"
  else
    native_up
  fi
}

run_down() {
  if [[ "${STACK_MODE}" == "docker" ]]; then
    docker_compose down "$@"
  else
    native_down
  fi
}

run_ps() {
  if [[ "${STACK_MODE}" == "docker" ]]; then
    docker_compose ps "$@"
  else
    native_ps
  fi
}

run_logs() {
  if [[ "${STACK_MODE}" == "docker" ]]; then
    docker_compose logs -f "$@"
  else
    native_logs
  fi
}

run_seed() {
  if [[ "${STACK_MODE}" == "docker" ]]; then
    docker_compose exec backend bash -c "poetry run python backend/manage.py seed_foundation_tenants --force"
  else
    native_seed
  fi
}

cmd="${1:-}"

if [[ -z "${cmd}" || "${cmd}" == "-h" || "${cmd}" == "--help" ]]; then
  usage
  exit 0
fi

shift || true

ensure_docker

case "${cmd}" in
  up)
    run_up "$@"
    ;;
  down)
    run_down "$@"
    ;;
  ps)
    run_ps "$@"
    ;;
  logs)
    run_logs "$@"
    ;;
  seed)
    run_seed "$@"
    ;;
  *)
    echo "Comando desconhecido: ${cmd}" >&2
    usage
    exit 1
    ;;
esac
