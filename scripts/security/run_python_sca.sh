#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-all}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
POETRY_BIN="${POETRY_BIN:-poetry}"
REPORT_DIR="${PYTHON_SCA_REPORT_DIR:-${ROOT_DIR}/artifacts/python-sca}"
mkdir -p "${REPORT_DIR}"

REQ_FILE="$(mktemp)"
cleanup() {
  rm -f "${REQ_FILE}"
}
trap cleanup EXIT

if command -v "${POETRY_BIN}" >/dev/null 2>&1; then
  # Poetry 2.x requer plugin de export; se falhar, faz fallback para freeze do env
  if ! "${POETRY_BIN}" export --with dev --format requirements.txt --output "${REQ_FILE}" >/dev/null 2>&1; then
    echo "Poetry export indisponível; usando freeze do ambiente virtual gerenciado pelo Poetry." >&2
    # Garante pip atualizado dentro do env
    "${POETRY_BIN}" run python -m pip install --quiet --upgrade pip
    "${POETRY_BIN}" run python - <<'PY'
import pkgutil, subprocess, sys
try:
    import pip
except Exception:
    pass
subprocess.check_call([sys.executable, '-m', 'pip', 'freeze'], stdout=open(sys.argv[1], 'w'))
PY
    "${REQ_FILE}"
  else
    "${POETRY_BIN}" run python -m pip install --quiet --upgrade pip
  fi
  "${POETRY_BIN}" run python -m pip install --quiet "pip-audit==2.7.3" "safety==3.3.4"
  PIP_AUDIT_CMD=("${POETRY_BIN}" "run" "pip-audit")
  SAFETY_CMD=("${POETRY_BIN}" "run" "safety")
else
  echo "Poetry não encontrado; utilizando ambiente global para dependências Python." >&2
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet "pip-audit==2.7.3" "safety==3.3.4"
  pip freeze > "${REQ_FILE}"
  PIP_AUDIT_CMD=("pip-audit")
  SAFETY_CMD=("safety")
fi

if [[ "${MODE}" == "all" || "${MODE}" == "pip-audit" ]]; then
  PIP_AUDIT_REPORT="${REPORT_DIR}/pip-audit.json"
  "${PIP_AUDIT_CMD[@]}" \
    --requirement "${REQ_FILE}" \
    --severity HIGH \
    --format json \
    --output "${PIP_AUDIT_REPORT}"
  echo "Relatório do pip-audit disponível em ${PIP_AUDIT_REPORT}."
fi

if [[ "${MODE}" == "all" || "${MODE}" == "safety" ]]; then
  SAFETY_REPORT="${REPORT_DIR}/safety.json"
  set +e
  "${SAFETY_CMD[@]}" check --stdin --json --full-report < "${REQ_FILE}" > "${SAFETY_REPORT}"
  SAFETY_EXIT=$?
  set -e

  if [[ ! -s "${SAFETY_REPORT}" ]]; then
    echo "Safety não gerou relatório JSON válido." >&2
    exit 1
  fi

  export SAFETY_REPORT_PATH="${SAFETY_REPORT}"
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
