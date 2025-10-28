import json
import subprocess
from pathlib import Path

import pytest


def test_k6_script_exports_foundation_api_throughput():
    script_path = Path("tests/performance/frontend-smoke.js")
    assert script_path.exists(), "Script de smoke deve existir."
    content = script_path.read_text(encoding="utf-8")
    assert "foundation_api_throughput" in content, "Script precisa publicar métrica foundation_api_throughput."
    assert "handleSummary" in content, "Script deve definir handleSummary para enviar métricas ao OTEL."


def test_alert_handler_creates_ticket_on_low_throughput(tmp_path):
    summary_path = tmp_path / "k6-summary.json"
    output_path = tmp_path / "alert.json"
    summary_path.write_text(
        json.dumps(
            {
                "metrics": {
                    "http_reqs": {"count": 120},
                    "vus_max": {"value": 10},
                },
                "state": {"testRunDurationMs": 60000},
                "options": {"summaryTrendStats": ["avg", "p(95)"], "thresholds": {}},
            }
        ),
        encoding="utf-8",
    )

    tsc_bin = Path("node_modules/.bin/tsc")
    assert tsc_bin.exists(), "Dependência typescript não instalada (node_modules/.bin/tsc)."
    subprocess.run([str(tsc_bin), "-p", "tsconfig.scripts.json"], check=True, cwd=Path.cwd())

    result = subprocess.run(
        [
            "node",
            "scripts/dist/observabilidade/alert-handler.js",
            "--summary",
            str(summary_path),
            "--output",
            str(output_path),
            "--threshold",
            "200",
        ],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, f"Script falhou: {result.stderr}"
    assert output_path.exists(), "Script deve gerar arquivo de saída."
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["metric"]["name"] == "foundation_api_throughput", "Saída deve referenciar métrica foundation_api_throughput."
    assert data["status"] in {"warning", "critical"}, "Status precisa refletir degradação."
    assert data["ticket"] == "@SC-001", "Ticket automático deve mencionar @SC-001."
