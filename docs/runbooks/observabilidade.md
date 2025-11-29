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
- Para evidências WORM ligadas a observabilidade, assine o payload (hash SHA-256 + assinatura assimétrica via KMS/Vault, ex.: RSA-PSS-SHA256 ou Ed25519) e valide a assinatura após upload antes de marcar como verificada.

## Seed_data (telemetria e gates)
- **Labels obrigatórias**: `tenant_id`, `environment`, `seed_run_id`, `manifest_version`, `mode`, `trace_id`, `span_id` em spans/logs/WORM; `pii_redacted=true` em logs. Eventos de criação de SeedRun são registrados com esses campos e reaproveitam trace/span do OTEL quando disponíveis.
- **Métricas/Spans**: histogramas `seed_run_duration_ms` e `seed_batch_latency_ms`, gauges `seed_rate_limit_remaining`/`seed_budget_remaining_pct` e status `seed_slo_status`. Dashboards versionados em `observabilidade/dashboards/seed-data.json` (Grafana/Loki).
- **Fail-close OTEL/Sentry**: CI executa `scripts/ci/seed-data-dry-run.sh` com `SIMULATE_TELEMETRY_FAILURE=1` para garantir saída 4; sem o flag roda dry-run baseline (stub seguro). Falha de export/redaction deve bloquear pipeline/execução.
- **Limpeza/PII**: `scripts/ci/check-audit-cleanliness.sh` valida logs/WORM com labels obrigatórias e reprova se detectar PII não redigida. Amostras canônicas em `observabilidade/data/seed-audit.log.jsonl` e `observabilidade/data/seed-worm-report.sample.json`.
- **k6 thresholds**: scripts `observabilidade/k6/seed-data-smoke.js` e `seed-data-load.js` carregam SLOs do manifesto (p95/p99/erro). Mantenha thresholds em linha com `docs/slo/seed-data.md`.

## Flags e métricas DORA (seed_data)
- `backend/apps/tenancy/feature_flags.py` bloqueia `canary` quando o manifesto não está em `mode=canary` (Problem Details `canary_flag_not_allowed`), garantindo rollout seguro.
- `SeedDORAMetrics` registra snapshot estruturado (`seed_dora_snapshot` via structlog) com `deployment_frequency_per_day`, `change_failure_rate`, `mttr_minutes`, `lead_time_minutes` e `rollback_rehearsed` por tenant. Fonte: tabela `tenancy_seed_run` (janela padrão = 14 dias).
- Use os snapshots para dashboards DORA e gatilhos de rollback ensaiado; falhas recorrentes devem acionar revisão de manifestos/feature flags antes de promover seeds carga/DR.
