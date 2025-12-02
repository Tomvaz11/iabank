# Catálogo de SLOs e Thresholds de Performance

Este documento consolida os Objetivos e Indicadores de Nível de Serviço (SLO/SLI) exigidos pela Constituição (Art. VI) e pelos ADRs. Ele deve ser versionado e atualizado sempre que novos domínios forem introduzidos.

| Domínio | SLI | SLO | Erro Tolerável | Threshold de Performance (k6) | Observações |
|---------|-----|-----|---------------|-------------------------------|-------------|
| API Loans / Fundação | Latência p95/p99 (GET /api/v1/loans/front) | p95 ≤ 600 ms (baseline), p99 ≤ 1 s; MTTR ≤ 1 h | Erro < 1% mensal (budget 1%); p95 500 ms apenas como stretch negociado | p95 < 600 ms e p99 < 1000 ms; erro < 1%; stretch opcional p95 < 500 ms | GameDay bimestral; budgets revisados a cada ciclo; alinhar alertas/ETAs ao spec |
| API Payments | Taxa de erro 5xx | ≤ 0.2% (mensal) | 100 incidentes por trimestre | p95 ≤ 400 ms | Monitorar budget antes de habilitar novos recursos |
| Backoffice Jobs | Throughput Celery | ≥ 98% jobs concluídos < 2 min | 2% jobs podem exceder 5 min | N/A (testes de carga via Celery worker bench) | Validar métricas no Prometheus |
| Frontend SPA | Web Vitals LCP p75 | ≤ 2.5 s (semanal) | 15% requests podem exceder 4 s | Lighthouse score ≥ 85 | Integrar métricas via Web Vitals SDK |

## Governança
- **Fonte de Verdade**: Este catálogo alimenta os pipelines (`docs/pipelines/ci-required-checks.md`) e deve ser referenciado por `/plan` ao definir metas de performance.
- **Processo de Atualização**: Qualquer alteração requer ADR ou emenda da constituição quando implicar mudança em políticas globais, incluindo ajustes de error budget.
- **Artefatos Relacionados**: Dashboards de observabilidade (Grafana/Sentry) e scripts de performance (`tests/performance/`); GameDays bimestrais devem ser agendados para validar budgets e playbooks de recuperação.

> Sempre que novos serviços forem introduzidos, adicione linhas à tabela com: métricas primárias, limites de budget e monitoramento correspondente.
