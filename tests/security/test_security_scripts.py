from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "snippet",
    [
        "semgrep",
        "--config",
    ],
)
def test_run_sast_utiliza_semgrep(snippet: str) -> None:
    content = Path("scripts/security/run_sast.sh").read_text(encoding="utf-8")
    assert (
        snippet in content
    ), f"O script de SAST deve utilizar Semgrep e receber configuração explícita ({snippet})."


def test_run_sast_define_politica_de_severidade() -> None:
    content = Path("scripts/security/run_sast.sh").read_text(encoding="utf-8")
    assert (
        "--severity" in content or "--severities" in content
    ), "Semgrep deve rodar com política explícita de severidade."


def test_semgrep_rules_file_existe() -> None:
    assert Path("scripts/security/semgrep.yml").exists(), "Configuração do Semgrep deve estar versionada."


def test_run_dast_invoca_zap_baseline() -> None:
    content = Path("scripts/security/run_dast.sh").read_text(encoding="utf-8")
    assert (
        "zap-baseline" in content
    ), "DAST deve utilizar o baseline do OWASP ZAP para escanear a stack local."


def test_script_sca_python_invoca_pip_audit_e_safety() -> None:
    script_path = Path("scripts/security/run_python_sca.sh")
    assert script_path.exists(), "Scanner SCA para Python deve existir."
    content = script_path.read_text(encoding="utf-8")
    assert "pip-audit" in content, "pip-audit precisa ser executado para dependências Python."
    assert "safety" in content, "Safety precisa ser executado para dependências Python."
