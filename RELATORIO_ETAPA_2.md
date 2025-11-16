# Relatório — Etapa 2 (Fases 6–7)

Período: execução local, conforme PLANO_VALIDACAO_E2E.md. Este relatório consolida os resultados da Etapa 2 desde o início desta conversa: Performance (k6) e Observabilidade (Prometheus/Grafana/OTEL), incluindo validações opcionais.

## Resumo Executivo
- Performance: k6 executado em dois cenários — 1 VU (local) e 50 VUs (opcional). O cenário 50 VUs atingiu throughput “ok” (50 req/s). O cenário local (1 VU) marcou “critical”, como esperado para validação brand/calibrada.
- Observabilidade: backend ativo, Prometheus com target `up`, Grafana provisionada, SC‑001 registrada com sucesso (201/200), spans OTEL enviados e aceitos pelo Collector (sem erros). Métrica SC‑001 confirmada via Prometheus (consulta sem rate) logo após o registro.

## Ambiente/Infra
- Backend + OTEL Collector: `docker compose -f infra/docker-compose.foundation.yml up -d backend otel-collector`
  - Observação: as portas 4317/4318 já estavam em uso por `foundation-otel-collector-1`. Utilizamos o Collector existente (nenhuma ação destrutiva).
- Prometheus: container `infra-prometheus` ativo (rede `infra_default`), apontando para `backend:8000` com `infra/prometheus.local.yml`.
- Grafana: container `infra-grafana` ativo com provisioning local em `infra/grafana/provisioning/**`.

## Fase 6 — Performance (k6)
Comandos executados:
1) `pnpm perf:smoke:local` (modo local, 1 VU, sem build)
2) `FOUNDATION_PERF_VUS=50 pnpm perf:smoke:ci` (opcional, com build, 50 VUs)
3) (Extra) Publicação via OTEL: `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 FOUNDATION_PERF_VUS=1 pnpm perf:smoke:ci`

Resultados (principais):
- Cenário 1 VU (local): throughput ≈ 1 req/s, status “critical”.
- Cenário 50 VUs: throughput = 50 req/s, status “ok”.
- Publicação via OTEL: sem erros no Collector (ver logs recentes abaixo).

Artefatos relevantes:
- `artifacts/perf/k6-smoke.json` (última execução)
- `artifacts/foundation-api-throughput.json` (sobrescrito pela última execução; reflete 1 VU). No momento do teste de 50 VUs, o throughput foi 50 req/s (status “ok”).

## Fase 7 — Observabilidade (Prometheus, Grafana, OTEL)
Passos executados:
1) Backend + Collector no ar (Collector já existente).
2) Prometheus “up” e coletando de `backend:8000/metrics`.
3) Grafana com dashboard “IABank Foundation — Observabilidade Local”.
4) Geração de tráfego e registro da SC‑001:
   - `GET /metrics` (10x) para aquecer séries.
   - `POST /api/v1/tenants/{uuid}/features/scaffold` com payload válido (checksums SHA‑256 e commit hash 40 hex). Respostas: 201 (novo) e 200 (idempotente/reuso).
5) Envio de spans via CLI do frontend: `pnpm --filter @iabank/frontend-foundation foundation:otel --endpoint http://localhost:4318/v1/traces ...` com `errors: []` e `exportedSpans: 1`.
6) Consultas Prometheus (as do painel):
   - HTTP por método: OK (resultados presentes)
   - Latência p95: OK
   - SC‑001: imediatamente após o primeiro registro o `rate()` em 5m pode retornar vazio; validado com média direta (sem rate), resultado presente para `feature_slug="loan-tracking-extra"`.

Artefatos relevantes:
- Collector (tail completo anterior): `artifacts/observability/collector.log`
- Collector (últimos 2 min, validação extra): `artifacts/observability/collector-recent.log` (0 errors / 0 warns)
- Consultas Prometheus: `artifacts/observability/prom-q1.json`, `prom-q2.json`, `prom-q3.json` (rate 5m logo após registro pode estar vazio), `prom-q3b.json` (média direta confirmando SC‑001)
- Grafana API: `artifacts/observability/grafana-health.json`, `grafana-dashboard.json`, `grafana-search.json`
- Métricas por tenant (header=path coerentes): `artifacts/observability/tenant-metrics.json`

Capturas do Grafana (render):
- `artifacts/observability/grafana-panel-1.png` — HTTP requests por método (req/s)
- `artifacts/observability/grafana-panel-2.png` — Erro 5xx (%)
- `artifacts/observability/grafana-panel-3.png` — Latência HTTP p95 (s)
- `artifacts/observability/grafana-panel-4.png` — SC‑001 — Duração média (min)

## Evidências (links rápidos)
- k6: `artifacts/perf/k6-smoke.json`, `artifacts/foundation-api-throughput.json`
- Prometheus target “up”: via API `/api/v1/targets` (container `infra-prometheus`)
- SC‑001 na exportação do backend: `GET http://localhost:8000/metrics` (série `sc_001_scaffolding_minutes_*`)
- SC‑001 no Prometheus (sem rate): `artifacts/observability/prom-q3b.json`
- Spans OTEL: `artifacts/observability/collector-recent.log` (sem erros/avisos)

## Ocorrências e Ajustes
- Porta ocupada (4317/4318): `infra-otel-collector` não subiu por conflito; Collector já existia (`foundation-otel-collector-1`). A solução foi reutilizar esse Collector (sem ações destrutivas), mantendo o endpoint em `http://localhost:4318`.
- Artefatos do k6: arquivos de resumo são sobrescritos a cada execução. Valores do cenário 50 VUs (throughput 50) foram registrados nos logs da sessão; os arquivos atuais refletem a execução final (1 VU). Se necessário, podemos reter ambos em nomes distintos numa próxima execução.
- Datasource Grafana: a datasource aponta `url: http://prometheus:9090`. Em ambientes onde o hostname difere, pode ser necessário um alias de rede. Aqui, as APIs do Grafana e consultas Prometheus funcionaram conforme esperado.

## Conclusão da Etapa 2
Todos os critérios de aceite das Fases 6–7 foram atendidos:
- k6 com status “ok” no cenário opcional (50 VUs) e artefatos gerados.
- Prometheus com target `up` e séries de HTTP/p95 disponíveis.
- SC‑001 registrada com sucesso; série exposta em `/metrics` e confirmada no Prometheus (consulta sem rate).
- Spans enviados ao Collector sem erros.

## Validações Extras (Executadas)
- k6 com publicação via OTEL (FOUNDATION_OTEL/OTEL_EXPORTER_OTLP_ENDPOINT): logs do Collector sem erros/avisos.
- Varrida de logs do Collector (janela 2 min): 0 errors / 0 warns.
- Consultas Prometheus equivalentes às do dashboard: HTTP por método, latência p95 e SC‑001 (sem rate) para validação imediata pós-registro.
- Verificação do endpoint `GET /api/v1/tenant-metrics/<tenant_uuid>/sc` com header `X-Tenant-Id` igual ao path: resposta 200; payload e paginação OK (lista vazia no momento, aguardando coleta adicional).

Próximo passo sugerido: avançar para a Etapa 3 (Fases 8–12) conforme o plano.
