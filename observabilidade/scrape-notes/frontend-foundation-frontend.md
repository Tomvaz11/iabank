# Scrape Notes — Frontend Foundation SPA

Este documento descreve como coletar as métricas de saturação da SPA servida pelo `frontend-foundation`. O objetivo é alimentar as gravações `foundation_frontend_cpu_percent` e `foundation_frontend_memory_percent`, que abastecem o painel `observabilidade/dashboards/frontend-foundation.json` e disparam os alertas do HPA (`T107`).

## Endpoint

- **Serviço:** `frontend-foundation-metrics`
- **Porta:** `9090` (`metrics`)
- **Caminho:** `/metrics`
- **Protocolo:** `http`

As métricas são expostas por um sidecar `prom/prometheus` embutido no `Deployment` do frontend. O sidecar utiliza descoberta automática de pods para coletar `container_cpu_usage_seconds_total` e `container_memory_usage_bytes`, aplicando `metric_relabel_configs` para restringir aos containers da SPA. A coleta é executada com `scrape_interval = 30s`.

## Configuração Prometheus

`infra/argocd/frontend-foundation/deployment.yaml` inclui o `ConfigMap` `frontend-foundation-prometheus-config` com o seguinte trecho relevante:

```yaml
scrape_configs:
  - job_name: frontend-foundation
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: frontend-foundation
    metric_relabel_configs:
      - source_labels: [container]
        action: keep
        regex: frontend|web
```

O `ServiceMonitor` (`infra/argocd/frontend-foundation/servicemonitor.yaml`) seleciona o service `frontend-foundation-metrics` e expõe o endpoint para o Prometheus central (Prometheus Operator).

## Métricas de Saturação

- `foundation_frontend_cpu_percent`: recording rule calculada a partir de `container_cpu_usage_seconds_total` e `kube_pod_container_resource_limits_cpu_cores`. Representa a porcentagem de CPU consumida pelo frontend em relação ao limite configurado para o pod.
- `foundation_frontend_memory_percent`: derivada de `container_memory_usage_bytes` e `kube_pod_container_resource_limits_memory_bytes`. Representa o consumo de memória frente ao limite definido no deployment.

Ambas as métricas são agregadas por cluster/namespace/pod e convertidas em percentual (%). Os dashboards utilizam o `max` no intervalo atual para acompanhar a saturação.

## Alertas

`infra/argocd/frontend-foundation/prometheus-rules.yaml` define:

- `FoundationFrontendSaturationWarning`: dispara quando `foundation_frontend_cpu_percent > 60` por 10 minutos. Severidade `warning`; acionar monitoramento do HPA.
- `FoundationFrontendSaturationCritical`: dispara quando `foundation_frontend_cpu_percent > 70` por 5 minutos. Severidade `critical`; acionar autoscaling imediato e abrir ticket `@SC-001`.

Ambos os alertas referenciam o runbook `docs/runbooks/frontend-foundation.md`.

## Validações

1. Executar `kubectl -n foundation port-forward svc/frontend-foundation-metrics 9090:9090` e consultar `http://localhost:9090/metrics` para garantir a presença das séries `foundation_frontend_cpu_percent` e `foundation_frontend_memory_percent`.
2. Confirmar no painel `Frontend Foundation — SC & UX` os widgets "Saturação CPU Frontend (%)" e "Saturação Memória Frontend (%)".
3. Forçar carga via `pnpm k6 run tests/performance/frontend-smoke.js` com `FOUNDATION_PERF_VUS=50` e observar a evolução das métricas e o firing dos alertas.
