#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-all}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
POETRY_BIN="${POETRY_BIN:-poetry}"
REPORT_DIR="${PYTHON_SCA_REPORT_DIR:-${ROOT_DIR}/artifacts/python-sca}"
mkdir -p "${REPORT_DIR}"

REQ_FILE="$(mktemp)"
TMP_SCAN_DIR="$(mktemp -d)"
cleanup() {
  rm -f "${REQ_FILE}"
  rm -rf "${TMP_SCAN_DIR}"
}
trap cleanup EXIT

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

create_tool_venv() {
  local name="$1"
  shift
  local dest="${TMP_SCAN_DIR}/${name}-venv"
  "${PYTHON_BIN}" -m venv "${dest}"
  "${dest}/bin/python" -m pip install --quiet --upgrade pip
  if (($#)); then
    "${dest}/bin/python" -m pip install --quiet "$@"
  fi
  echo "${dest}"
}

RUN_PIP_AUDIT=false
RUN_SAFETY=false
case "${MODE}" in
  all)
    RUN_PIP_AUDIT=true
    RUN_SAFETY=true
    ;;
  pip-audit)
    RUN_PIP_AUDIT=true
    ;;
  safety)
    RUN_SAFETY=true
    ;;
  *)
    echo "Modo desconhecido '${MODE}'. Use 'all', 'pip-audit' ou 'safety'." >&2
    exit 2
    ;;
esac

SAFETY_VERSION_WITH_API="3.6.2"
SAFETY_VERSION_OFFLINE="2.3.5"
if [[ -n "${SAFETY_API_KEY:-}" ]]; then
  SAFETY_PKG_VERSION="${SAFETY_VERSION_WITH_API}"
else
  # Safety 3.x exige autenticação; com fallback offline usamos a série 2.3.x.
  SAFETY_PKG_VERSION="${SAFETY_VERSION_OFFLINE}"
fi

if command -v "${POETRY_BIN}" >/dev/null 2>&1; then
  # Em Poetry 1.8.x, o comando export depende de plugin; se indisponível, faz fallback para freeze.
  if ! "${POETRY_BIN}" export --with dev --format requirements.txt --output "${REQ_FILE}" >/dev/null 2>&1; then
    echo "Poetry export indisponível; usando freeze do ambiente virtual gerenciado pelo Poetry." >&2
    "${POETRY_BIN}" run python -m pip install --quiet --upgrade pip
    # Gera requirements a partir do ambiente do Poetry
    "${POETRY_BIN}" run python -m pip freeze > "${REQ_FILE}"
  else
    "${POETRY_BIN}" run python -m pip install --quiet --upgrade pip
  fi
else
  echo "Poetry não encontrado; utilizando ambiente global para dependências Python." >&2
  "${PYTHON_BIN}" -m pip install --quiet --upgrade pip
  "${PYTHON_BIN}" -m pip freeze > "${REQ_FILE}"
fi

if [[ "${RUN_PIP_AUDIT}" == true ]]; then
  PIP_AUDIT_VENV="$(create_tool_venv "pip-audit" "pip-audit==2.7.3")"
  PIP_AUDIT_CMD=("${PIP_AUDIT_VENV}/bin/pip-audit")
fi

if [[ "${RUN_SAFETY}" == true ]]; then
  SAFETY_VENV="$(create_tool_venv "safety" "safety==${SAFETY_PKG_VERSION}")"
  SAFETY_CMD=("${SAFETY_VENV}/bin/safety")
fi

if [[ "${RUN_PIP_AUDIT}" == true ]]; then
  PIP_AUDIT_REPORT="${REPORT_DIR}/pip-audit.json"
  # Executa a partir de um diretório vazio para evitar que a CLI infira project_path
  # quando há um pyproject.toml no CWD, o que conflita com -r/--requirement em algumas versões.
  (
    cd "${TMP_SCAN_DIR}" >/dev/null
    "${PIP_AUDIT_CMD[@]}" \
      --requirement "${REQ_FILE}" \
      --format json \
      --output "${PIP_AUDIT_REPORT}" \
      --progress-spinner off
  )
  echo "Relatório do pip-audit disponível em ${PIP_AUDIT_REPORT}."
fi

if [[ "${RUN_SAFETY}" == true ]]; then
  # Hardening do ambiente para saídas determinísticas e UTF-8
  export PYTHONUTF8=1
  export LANG=C
  export LC_ALL=C
  export CI=1
  export PYTHONUNBUFFERED=1
  export PYTHONIOENCODING=UTF-8
  export SAFETY_REQUEST_TIMEOUT=${SAFETY_REQUEST_TIMEOUT:-30}

  SAFETY_DIR="${REPORT_DIR}"
  mkdir -p "${SAFETY_DIR}"
  SAFETY_JSON_TMP="${SAFETY_DIR}/safety.json.tmp"
  SAFETY_JSON_FINAL="${SAFETY_DIR}/safety.json"
  SAFETY_STDERR_LOG="${SAFETY_DIR}/safety.stderr.log"

  # Executa Safety em modo JSON estrito via stdout e captura stderr separado
  set +e
  # Descobre suporte à flag de telemetria opcional nesta versão (best-effort)
  SAFETY_FLAGS=()
  if "${SAFETY_CMD[@]}" scan --help 2>/dev/null | grep -q -- '--disable-optional-telemetry'; then
    SAFETY_FLAGS+=("--disable-optional-telemetry")
  fi
  SAFETY_JSON_FORMAT_FLAG=()
  if "${SAFETY_CMD[@]}" check --help 2>/dev/null | grep -q -- '--json-output-format'; then
    SAFETY_JSON_FORMAT_FLAG=(--json-output-format 1.1)
  fi

  # Registrar versão do Safety para diagnóstico
  { "${SAFETY_CMD[@]}" --version || true; } >>"${SAFETY_STDERR_LOG}" 2>&1

  SAFETY_SUBCOMMAND="scan"
  if [[ -z "${SAFETY_API_KEY:-}" ]]; then
    SAFETY_SUBCOMMAND="check"
    echo "[Safety] SAFETY_API_KEY não definido; usando fallback 'check' (offline)." >&2
  fi

  if [[ "${SAFETY_SUBCOMMAND}" == "scan" ]]; then
    "${SAFETY_CMD[@]}" scan \
      -r "${REQ_FILE}" \
      --output json \
      ${SAFETY_FLAGS[@]+"${SAFETY_FLAGS[@]}"} \
      >"${SAFETY_JSON_TMP}" 2>"${SAFETY_STDERR_LOG}"
  else
    "${SAFETY_CMD[@]}" check \
      --file "${REQ_FILE}" \
      --output json \
      ${SAFETY_JSON_FORMAT_FLAG[@]+"${SAFETY_JSON_FORMAT_FLAG[@]}"} \
      >"${SAFETY_JSON_TMP}" 2>"${SAFETY_STDERR_LOG}"
  fi
  SAFETY_EXIT=$?
  if [[ ${SAFETY_EXIT} -ne 0 ]]; then
    # Alguns ambientes retornam 1 quando encontra vulnerabilidades; aceitável para processamento
    true
  fi
  set -e

  # Validar JSON antes de mover para o arquivo final
  "${PYTHON_BIN}" - <<PY
import json, sys, pathlib
tmp = pathlib.Path(r"${SAFETY_JSON_TMP}")
err = pathlib.Path(r"${SAFETY_STDERR_LOG}")
raw = ''
if tmp.exists():
    raw = tmp.read_text(encoding='utf-8')

def try_parse(text: str):
    try:
        json.loads(text)
        return True
    except Exception:
        return False

if not raw.strip():
    print("ERRO: safety.json vazio; veja STDERR a seguir.", file=sys.stderr)
    try:
        est = err.read_text(encoding='utf-8')[:16000]
    except Exception:
        est = ''
    if est:
        print("\n--- STDERR do Safety ---\n" + est, file=sys.stderr)
    sys.exit(1)

if not try_parse(raw):
    # Tenta saneamento: recorta a partir do primeiro '{' até o último '}'
    start = raw.find('{')
    end = raw.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = raw[start:end+1]
        if try_parse(candidate):
            tmp.write_text(candidate, encoding='utf-8')
        else:
            print("ERRO: safety.json inválido mesmo após saneamento.", file=sys.stderr)
            print("\n--- Amostra do stdout capturado (início) ---\n" + raw[:1000], file=sys.stderr)
            try:
                est = err.read_text(encoding='utf-8')[:16000]
            except Exception:
                est = ''
            if est:
                print("\n--- STDERR do Safety ---\n" + est, file=sys.stderr)
            sys.exit(1)
    else:
        print("ERRO: safety.json inválido: não foi encontrado bloco JSON.", file=sys.stderr)
        print("\n--- Amostra do stdout capturado (início) ---\n" + raw[:1000], file=sys.stderr)
        try:
            est = err.read_text(encoding='utf-8')[:16000]
        except Exception:
            est = ''
        if est:
            print("\n--- STDERR do Safety ---\n" + est, file=sys.stderr)
        sys.exit(1)
PY
  mv -f "${SAFETY_JSON_TMP}" "${SAFETY_JSON_FINAL}"

  export SAFETY_REPORT_PATH="${SAFETY_JSON_FINAL}"
  export SAFETY_EXIT_CODE="${SAFETY_EXIT}"
  SAFETY_STATUS="$(
    "${PYTHON_BIN}" <<'PY'
import json
import os
import sys

report_path = os.environ["SAFETY_REPORT_PATH"]
exit_code = int(os.environ["SAFETY_EXIT_CODE"])
with open(report_path, "r", encoding="utf-8") as handler:
    payload = json.load(handler)

def iter_vulns(item):
    if isinstance(item, dict):
        if "vulnerabilities" in item:
            for sub in item["vulnerabilities"]:
                yield from iter_vulns(sub)
        if "issues" in item:
            for sub in item["issues"]:
                yield from iter_vulns(sub)
        if "results" in item:
            for sub in item["results"]:
                yield from iter_vulns(sub)
        if "advisories" in item:
            for sub in item["advisories"]:
                yield from iter_vulns(sub)
        if item.get("package"):
            yield item
    elif isinstance(item, list):
        for sub in item:
            yield from iter_vulns(sub)

def resolve_severity(vuln):
    sev = vuln.get("severity")
    if isinstance(sev, dict):
        sev = sev.get("name") or sev.get("level") or sev.get("value")
    if isinstance(sev, list) and sev:
        sev = sev[0]
    if isinstance(sev, str):
        return sev.lower()
    cvss = vuln.get("cvss", {})
    if isinstance(cvss, dict):
        score = cvss.get("base_score")
        if score is not None:
            try:
                score = float(score)
            except (TypeError, ValueError):
                return None
            if score >= 9.0:
                return "critical"
            if score >= 7.0:
                return "high"
            if score >= 4.0:
                return "medium"
    return None

has_high = False
details = []
for vulnerability in iter_vulns(payload):
    severity = resolve_severity(vulnerability)
    if severity:
        details.append(f"{vulnerability.get('package', {}).get('name', 'unknown')}:{severity}")
    if severity in {"high", "critical"}:
        has_high = True

if exit_code not in (0, 1):
    print("ERROR", exit_code, ";".join(details))
    sys.exit(0)

if has_high:
    print("FAIL", ";".join(details))
else:
    print("OK", ";".join(details))
PY
  )"

  SAFETY_STATUS_CODE="$(cut -d' ' -f1 <<< "${SAFETY_STATUS}")"
  SAFETY_STATUS_DETAILS="$(cut -d' ' -f2- <<< "${SAFETY_STATUS}")"

  if [[ "${SAFETY_STATUS_CODE}" == "ERROR" ]]; then
    echo "Safety falhou com erro (${SAFETY_STATUS_DETAILS})." >&2
    exit "${SAFETY_EXIT}"
  fi

  if [[ "${SAFETY_STATUS_CODE}" == "FAIL" ]]; then
    echo "Safety encontrou vulnerabilidades High/Critical: ${SAFETY_STATUS_DETAILS}" >&2
    exit 1
  fi

  echo "Safety concluído sem vulnerabilidades High/Critical."
fi
