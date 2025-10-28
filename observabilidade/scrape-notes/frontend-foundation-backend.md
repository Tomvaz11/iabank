# Scrape Notes — Frontend Foundation Backend

Estas anotações padronizam a coleta de métricas Prometheus expostas pelo backend da fundação (`django-prometheus`). Utilizamos o endpoint `/metrics`, habilitado em `backend/config/urls.py`, para alimentar os dashboards SC-001–SC-005 e alertas operacionais descritos no runbook de observabilidade.

## Endpoint

- **Base URL:** dependerá do ambiente (`https://api.iabank.com` em produção, `https://staging-api.iabank.com` em homologação, `http://backend:8000` em dev/CI)
- **Caminho:** `/metrics`
- **Autenticação:** não aplicável (endpoint protegido por rede interna)
- **Formato:** `text/plain; version=0.0.4`

## Scrape Config (Prometheus)

```yaml
- job_name: frontend-foundation-backend
  scrape_interval: 30s
  scrape_timeout: 10s
  metrics_path: /metrics
  scheme: https # use http em dev/local
  static_configs:
    - targets:
        - api.iabank.com
      labels:
        service: frontend-foundation-backend
        env: production
  tls_config:
    insecure_skip_verify: false
```

> Atualize `targets`, `scheme` e labels conforme o ambiente (staging/local). Em clusters Kubernetes, prefira `kubernetes_sd_configs` com `relabel_configs` para anexar `namespace` e `pod`.

## Métricas Relevantes

- `django_http_requests_total` — contagem de requisições HTTP, útil para throughput (`foundation_api_throughput` deriva deste contador).
- `django_http_requests_latency_seconds` — histograma de latência por view; acompanhe p95/p99 nos dashboards.
- `django_db_new_connections_total` — quantidade de conexões de banco; usado nos alertas de saturação.
- `django_celery_tasks_total` — contagem de tasks Celery emitidas pelo backend (suporte ao scaffolding).

Todas as métricas carregam as labels padrão do `django-prometheus` (`method`, `view`, `status`, `tenant` quando disponível). Certifique-se de propagar `X-Tenant-Id` nas chamadas internas para manter a cardinalidade controlada.

## Alertas

- **Disponibilidade:** `absent(django_http_requests_total{service="frontend-foundation-backend"}[5m])` → incidente.
- **Latência:** `histogram_quantile(0.95, sum(rate(django_http_requests_latency_seconds_bucket[5m])) by (le, view)) > 0.8` → degradação.
- **Erros:** `sum(rate(django_http_requests_total{status=~"5.."}[5m])) / sum(rate(django_http_requests_total[5m])) > 0.05` → falha.

Os alertas devem acionar o runbook `docs/runbooks/observabilidade.md` e etiquetar incidentes com `@SC-005`.

