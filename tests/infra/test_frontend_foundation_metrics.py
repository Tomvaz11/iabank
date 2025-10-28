import json
from pathlib import Path


def read_manifest(path: Path) -> str:
    assert path.exists(), f"Manifesto {path} não encontrado."
    return path.read_text(encoding="utf-8")


def test_deployment_declares_prometheus_sidecar():
    manifest = read_manifest(Path("infra/argocd/frontend-foundation/deployment.yaml"))
    assert "kind: Deployment" in manifest and "name: frontend-foundation" in manifest, "Deployment frontend-foundation deve existir."
    assert "name: metrics-sidecar" in manifest, "Sidecar Prometheus precisa estar declarado."
    assert "image: prom/prometheus" in manifest, "Sidecar deve usar imagem do Prometheus."
    assert "containerPort: 9090" in manifest, "Sidecar deve expor porta 9090."
    assert "name: prometheus-config" in manifest, "Sidecar precisa montar ConfigMap prometheus-config."


def test_configmap_exposes_prometheus_configuration():
    manifest = read_manifest(Path("infra/argocd/frontend-foundation/deployment.yaml"))
    assert "kind: ConfigMap" in manifest and "name: frontend-foundation-prometheus-config" in manifest, "ConfigMap prometheus-config deve existir."
    assert "prometheus.yml" in manifest, "ConfigMap precisa conter arquivo prometheus.yml."
    assert "scrape_configs" in manifest, "Config do Prometheus deve definir scrape_configs."
    assert "frontend-foundation" in manifest, "Config deve filtrar pods do frontend-foundation."


def test_servicemonitor_targets_metrics_port():
    manifest = read_manifest(Path("infra/argocd/frontend-foundation/servicemonitor.yaml"))
    assert "kind: ServiceMonitor" in manifest, "ServiceMonitor precisa existir."
    assert "port: metrics" in manifest, "Endpoint do ServiceMonitor deve mirar a porta metrics."
    assert "path: /metrics" in manifest, "Endpoint do ServiceMonitor deve usar caminho /metrics."


def test_prometheus_rule_records_cpu_and_memory_and_alerts():
    manifest = read_manifest(Path("infra/argocd/frontend-foundation/prometheus-rules.yaml"))
    assert "kind: PrometheusRule" in manifest, "PrometheusRule precisa existir."
    assert "record: foundation_frontend_cpu_percent" in manifest, "Recording rule para CPU deve existir."
    assert "record: foundation_frontend_memory_percent" in manifest, "Recording rule para memória deve existir."
    assert "container_cpu_usage_seconds_total" in manifest, "Expressão de CPU deve derivar de container_cpu_usage_seconds_total."
    assert "container_memory_usage_bytes" in manifest, "Expressão de memória deve derivar de container_memory_usage_bytes."
    assert "alert: FoundationFrontendSaturationCritical" in manifest, "Alerta crítico deve existir."
    assert "alert: FoundationFrontendSaturationWarning" in manifest, "Alerta de aviso deve existir."
    assert "@SC-001" in manifest, "Alertas precisam mencionar follow-up @SC-001."


def test_dashboard_contains_cpu_and_memory_panels():
    dashboard_path = Path("observabilidade/dashboards/frontend-foundation.json")
    assert dashboard_path.exists(), "Dashboard principal deve existir."
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))

    expressions = []
    for panel in dashboard.get("panels", []):
        for target in panel.get("targets", []):
            expr = target.get("expr")
            if expr:
                expressions.append(expr)

    assert any("foundation_frontend_cpu_percent" in expr for expr in expressions), "Painel precisa monitorar foundation_frontend_cpu_percent."
    assert any("foundation_frontend_memory_percent" in expr for expr in expressions), "Painel precisa monitorar foundation_frontend_memory_percent."
    assert any("foundation_api_throughput" in expr for expr in expressions), "Painel precisa monitorar foundation_api_throughput."


def test_scrape_notes_document_frontend_metrics():
    notes_path = Path("observabilidade/scrape-notes/frontend-foundation-frontend.md")
    assert notes_path.exists(), "Scrape notes para o frontend devem ser documentadas."
    content = notes_path.read_text(encoding="utf-8")
    assert "foundation_frontend_cpu_percent" in content, "Scrape notes deve citar métrica foundation_frontend_cpu_percent."
    assert "foundation_frontend_memory_percent" in content, "Scrape notes deve citar métrica foundation_frontend_memory_percent."
