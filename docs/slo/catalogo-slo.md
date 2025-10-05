# Catálogo de SLOs e Thresholds de Performance

Este documento consolida os Objetivos e Indicadores de Nível de Serviço (SLO/SLI) exigidos pela Constituição (Art. VI) e pelos ADRs. Ele deve ser versionado e atualizado sempre que novos domínios forem introduzidos.

| Domínio | SLI | SLO | Erro Tolerável | Threshold de Performance (k6) | Observações |
|---------|-----|-----|---------------|-------------------------------|-------------|
| API Loans | Latência p95 (GET /api/v1/loans/) | ≤ 500 ms (mensal) | 0.1% requests acima de 2s | Req/s alvo: 100; p99 ≤ 750 ms | Configurar teste k6 `scenarios/loans.js` |
| API Payments | Taxa de erro 5xx | ≤ 0.2% (mensal) | 100 incidentes por trimestre | p95 ≤ 400 ms | Monitorar budget antes de habilitar novos recursos |
| Backoffice Jobs | Throughput Celery | ≥ 98% jobs concluídos < 2 min | 2% jobs podem exceder 5 min | N/A (testes de carga via Celery worker bench) | Validar métricas no Prometheus |
| Frontend SPA | Web Vitals LCP p75 | ≤ 2.5 s (semanal) | 15% requests podem exceder 4 s | Lighthouse score ≥ 85 | Integrar métricas via Web Vitals SDK |

## Governança
- **Fonte de Verdade**: Este catálogo alimenta os pipelines (`docs/pipelines/ci-required-checks.md`) e deve ser referenciado por `/plan` ao definir metas de performance.
- **Processo de Atualização**: Qualquer alteração requer ADR ou emenda da constituição quando implicar mudança em políticas globais.
- **Artefatos Relacionados**: Dashboards de observabilidade (Grafana/Sentry) e scripts de performance (`tests/performance/`).

> Sempre que novos serviços forem introduzidos, adicione linhas à tabela com: métricas primárias, limites de budget e monitoramento correspondente.
