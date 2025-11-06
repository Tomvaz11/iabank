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
  "${POETRY_BIN}" run python -m pip install --quiet "pip-audit==2.7.3" "safety==3.6.2"
  # Resolve binários absolutos dentro do venv do Poetry para permitir executar fora do CWD do projeto
  PIP_AUDIT_BIN="$(${POETRY_BIN} run which pip-audit)"
  SAFETY_BIN="$(${POETRY_BIN} run which safety)"
  if [[ -z "${PIP_AUDIT_BIN}" || ! -x "${PIP_AUDIT_BIN}" ]]; then
    echo "pip-audit não encontrado no ambiente do Poetry." >&2
    exit 1
  fi
  if [[ -z "${SAFETY_BIN}" || ! -x "${SAFETY_BIN}" ]]; then
    echo "safety não encontrado no ambiente do Poetry." >&2
    exit 1
  fi
  PIP_AUDIT_CMD=("${PIP_AUDIT_BIN}")
  SAFETY_CMD=("${SAFETY_BIN}")
else
  echo "Poetry não encontrado; utilizando ambiente global para dependências Python." >&2
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet "pip-audit==2.7.3" "safety==3.6.2"
  pip freeze > "${REQ_FILE}"
  PIP_AUDIT_CMD=("pip-audit")
  SAFETY_CMD=("safety")
fi

if [[ "${MODE}" == "all" || "${MODE}" == "pip-audit" ]]; then
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

if [[ "${MODE}" == "all" || "${MODE}" == "safety" ]]; then
  # Hardening do ambiente para saídas determinísticas e UTF-8
  export PYTHONUTF8=1
  export LANG=C
  export LC_ALL=C

  SAFETY_DIR="${REPORT_DIR}"
  mkdir -p "${SAFETY_DIR}"
  SAFETY_JSON_TMP="${SAFETY_DIR}/safety.json.tmp"
  SAFETY_JSON_FINAL="${SAFETY_DIR}/safety.json"
  SAFETY_STDERR_LOG="${SAFETY_DIR}/safety.stderr.log"

  # Executa Safety em modo JSON estrito via stdout e captura stderr separado
  set +e
  if "${SAFETY_CMD[@]}" --version 2>/dev/null | grep -Eq "\b3\.|\b2\."; then
    # Preferir o subcomando moderno 'scan'; fazer fallback para 'check' se necessário
    "${SAFETY_CMD[@]}" scan \
      -r "${REQ_FILE}" \
      --output json \
      --disable-optional-telemetry \
      >"${SAFETY_JSON_TMP}" 2>"${SAFETY_STDERR_LOG}"
    SAFETY_EXIT=$?
    if [[ ${SAFETY_EXIT} -ne 0 ]]; then
      # Alguns ambientes retornam 1 quando encontra vulnerabilidades; aceitável para processamento
      true
    fi
    # Se 'scan' não existir (versão mais antiga), tentar 'check'
    if [[ ! -s "${SAFETY_JSON_TMP}" ]]; then
      "${SAFETY_CMD[@]}" check \
        -r "${REQ_FILE}" \
        --output json \
        --disable-optional-telemetry \
        >"${SAFETY_JSON_TMP}" 2>>"${SAFETY_STDERR_LOG}"
      SAFETY_EXIT=$?
    fi
  else
    # Versões fora do padrão — tentativa conservadora
    "${SAFETY_CMD[@]}" check \
      -r "${REQ_FILE}" \
      --output json \
      --disable-optional-telemetry \
      >"${SAFETY_JSON_TMP}" 2>"${SAFETY_STDERR_LOG}"
    SAFETY_EXIT=$?
  fi
  set -e

  # Validar JSON antes de mover para o arquivo final
  python - <<PY
import json, sys, pathlib
tmp = pathlib.Path(r"${SAFETY_JSON_TMP}")
err = pathlib.Path(r"${SAFETY_STDERR_LOG}")
try:
    raw = tmp.read_text(encoding='utf-8')
    json.loads(raw)
except Exception as e:
    print("ERRO: safety.json inválido:", e, file=sys.stderr)
    try:
        sample = tmp.read_text(encoding='utf-8')[:1000]
    except Exception:
        sample = '<sem conteúdo>'
    print("\n--- Amostra do stdout capturado (início) ---\n" + sample, file=sys.stderr)
    try:
        est = err.read_text(encoding='utf-8')[:4000]
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
    python <<'PY'
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
