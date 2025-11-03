# Runbook: Observabilidade e Telemetria Padronizada

Executa o **ADR-012** alinhado ao Artigo VII da Constituição.

> Diretórios em português (`observabilidade/`) armazenam dashboards versionados; scripts de utilidade continuam em `scripts/observability/` (nome legado em inglês).

## Verificações Diárias
1. **Logs estruturados**
   - Inspecione amostras no stack ELK/Sentry para confirmar formato JSON e ausência de PII.
   - Execute `python scripts/observability/check_structlog.py <arquivo_de_log>` para validar máscaras automaticamente.
2. **Traces OpenTelemetry**
   - Garanta propagação `traceparent`/`tracestate` entre frontend e backend.
   - Verifique no collector que exportadores estão ativos (gRPC/HTTP).
3. **Métricas (django-prometheus)**
   - Dashboard `SLO Core` deve exibir p95/p99 e throughput com dados recentes (<5 min).
   - Alertas de erro e saturação precisam estar verdes.
   - Conferir notas de coleta em `observabilidade/scrape-notes/frontend-foundation-backend.md`.

## Revisões Mensais
- Auditar dashboards de SLO para cada serviço crítico.
- Revisar configuração do processor de redaction (ver ADR-010).
- Atualizar mapa de dependências no runbook com novos serviços instrumentados.

## Incidentes
- Quando alertas DORA/SLO dispararem, siga `docs/runbooks/incident-response.md`.
- Registre post-mortem com os spans relevantes.
