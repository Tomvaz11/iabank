import json
from pathlib import Path

import yaml


def load_workflow() -> dict:
    with open(".github/workflows/ci/frontend-foundation.yml", "r", encoding="utf-8") as handler:
        return yaml.safe_load(handler)


def test_security_job_contains_sbom_and_audits() -> None:
    workflow = load_workflow()
    security_job = workflow["jobs"]["security"]
    steps = [step["name"] for step in security_job["steps"]]

    assert any("SBOM" in name for name in steps), "O job de segurança deve gerar SBOM CycloneDX."
    assert any(
        "pnpm audit" in step.get("run", "") for step in security_job["steps"]
    ), "O job de segurança deve executar pnpm audit."


def test_security_job_usa_semgrep_para_sast() -> None:
    workflow = load_workflow()
    security_job = workflow["jobs"]["security"]
    semgrep_steps = [
        step
        for step in security_job["steps"]
        if "SAST" in step["name"] and "run_sast.sh" in step.get("run", "")
    ]

    assert semgrep_steps, "O job de segurança deve invocar o script de SAST baseado em Semgrep."


def test_security_job_roda_zap_baseline() -> None:
    workflow = load_workflow()
    security_job = workflow["jobs"]["security"]
    zap_steps = [
        step
        for step in security_job["steps"]
        if "ZAP" in step["name"] or "zap-baseline.py" in step.get("run", "")
    ]

    assert zap_steps, "O job de segurança deve executar o baseline do OWASP ZAP."


def test_security_job_roda_pip_audit_e_safety() -> None:
    workflow = load_workflow()
    security_job = workflow["jobs"]["security"]
    step_names = [step["name"] for step in security_job["steps"]]

    assert any("pip-audit" in name for name in step_names), "pip-audit deve rodar no job de segurança."
    assert any("Safety" in name for name in step_names), "Safety deve rodar no job de segurança."


def test_pnpm_audit_configurado_para_high() -> None:
    package_json = json.loads(Path("package.json").read_text(encoding="utf-8"))
    audit_script = package_json["scripts"]["audit:frontend"]

    assert (
        "--audit-level=high" in audit_script
    ), "pnpm audit precisa falhar para vulnerabilidades High/Critical."
