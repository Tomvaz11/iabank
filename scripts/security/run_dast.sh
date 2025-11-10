#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker é obrigatório para executar o baseline do OWASP ZAP." >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl é necessário para validar o endpoint alvo antes do scan." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
POETRY_BIN="${POETRY_BIN:-poetry}"
TARGET_URL="${ZAP_BASELINE_TARGET:-http://127.0.0.1:8000/health}"
REPORT_DIR="${ZAP_BASELINE_REPORT_DIR:-${ROOT_DIR}/artifacts/zap}"
mkdir -p "${REPORT_DIR}"

if ! command -v "${POETRY_BIN}" >/dev/null 2>&1; then
  echo "Poetry não encontrado (procure por ${POETRY_BIN}). Defina POETRY_BIN para o binário correto." >&2
  exit 1
fi

echo "Aplicando migrações do Django para preparar o alvo DAST..."
"${POETRY_BIN}" run python backend/manage.py migrate --noinput

echo "Iniciando servidor Django para o scan ZAP..."
"${POETRY_BIN}" run python backend/manage.py runserver 0.0.0.0:8000 >/tmp/django-zap.log 2>&1 &
SERVER_PID=$!

cleanup() {
  if kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    kill "${SERVER_PID}"
  fi
}
trap cleanup EXIT

echo "Aguardando o serviço responder em ${TARGET_URL}..."
for _ in {1..30}; do
  if curl --fail --silent "${TARGET_URL}" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! curl --fail --silent "${TARGET_URL}" >/dev/null 2>&1; then
  echo "Não foi possível alcançar ${TARGET_URL} após aguardar o serviço. Verifique se o servidor iniciou corretamente." >&2
  exit 1
fi

echo "Executando OWASP ZAP baseline contra ${TARGET_URL}..."
# Executa o baseline e tolera código 2 (apenas WARN). Falha em qualquer FAIL.
set +e
docker run --rm \
  --pull=always \
  --network=host \
  -u 0:0 \
  -w /zap/wrk \
  -v "${REPORT_DIR}:/zap/wrk" \
  ghcr.io/zaproxy/zaproxy:stable \
  /zap/zap-baseline.py \
  -t "${TARGET_URL}" \
  -a \
  -J zap-baseline.json \
  -w zap-warnings.md \
  -r zap-report.html \
  -x zap-report.xml \
  -m 5 ${ZAP_BASELINE_EXTRA_ARGS:-}
status=$?
set -e
if [ "$status" -eq 2 ]; then
  echo "[DAST] Somente WARN foram detectados — registrando como sucesso (sem FAILs)."
  status=0
fi
echo "Conteúdo do diretório de relatórios (${REPORT_DIR}):"
ls -la "${REPORT_DIR}" || true
exit "$status"

echo "Relatórios ZAP armazenados em ${REPORT_DIR}."
