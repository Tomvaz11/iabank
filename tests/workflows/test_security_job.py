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
