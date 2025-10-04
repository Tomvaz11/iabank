# 12. Observabilidade e Telemetria Padronizada

**Status:** Aprovado

**Contexto:** O Artigo VII (Observabilidade) determina o uso de OpenTelemetry, correlação W3C Trace Context e logs estruturados. As diretrizes de observabilidade da plataforma definem ferramentas específicas (structlog, django-prometheus, Sentry) e exigem alertas orientados a SLO. Para manter a Constituição focada em princípios, estes detalhes são formalizados neste ADR.

**Decisão:**
- **Bibliotecas de referência:**
  - Backend Django utiliza **structlog** para logging JSON contextualizado.
  - Métricas são expostas via **django-prometheus**.
  - Alertas de erros e anomalias são centralizados no **Sentry**, integrado a canais de incidentes.
- **Coleta OpenTelemetry:** Aplicações DEVE usar o SDK OpenTelemetry padrão para traces e métricas, propagando `traceparent`/`tracestate` e exportando para o collector central.
- **Dashboards SLO:** Para cada serviço crítico, dashboards contendo p95/p99 de latência, throughput e saturação são obrigatórios no provedor de observabilidade.
- **Redação de atributos sensíveis:** O collector aplica processadores que removem/mask campos marcados como PII (ver ADR-010).

**Consequências:**
- Projetos que não usarem as bibliotecas acima devem propor ADR alternativo antes da implementação.
- Pipelines de CI precisam validar a configuração de tracing e métricas (ex.: testes que verificam exportação de spans/logs).
- Alertas do Sentry devem ser vinculados aos runbooks descritos na base de operações.

**Referências Operacionais:**
- Runbook: `docs/runbooks/observabilidade.md`
- Checklist de CI: `docs/pipelines/ci-required-checks.md`
