# SLO/SLI - seed_data

- **Escopo**: endpoint `/api/v1/seed-profiles/validate` (pre-execucao) e comando/worker `seed_data` (baseline/carga/DR). Valores alimentam BudgetRateLimit e gates k6.
- **Metodologia**: SLIs extraidos de metricas OTEL (`seed.run.duration_ms`, `seed.validate.duration_ms`, `seed_rate_limit_remaining`, `seed_budget_remaining`). Erros usam Problem Details (`status>=400`).
- **Targets** (herdam manifesto v1; limites iguais para `carga` e `dr`):

| Ambiente | SLI validacao p95 (ms) | SLI validacao p99 (ms) | Throughput alvo (rps) | Erro/429 orcamentado | Janela | Run p95 (min) | Run p99 (min) |
|---|---|---|---|---|---|---|---|
| dev | 4000 | 6000 | 2 | 2% | 7d | 5 | 8 |
| homolog | 4500 | 6500 | 3 | 2% | 7d | 10 | 12 |
| staging/perf | 5000 | 7000 | 5 | 1.5% | 7d | 20 | 25 |

- **Budget**: alertar em 80% (`error_budget_pct` ou `budget_cost_cap`), abortar em 100%. Runs com `mode=baseline` respeitam caps Q11; `carga/dr` abortam ao exceder budget ou RPO/RTO.
- **Headers obrigatorios**: `RateLimit-*`, `Retry-After`, `Idempotency-Key`. Ausencia conta como erro para o budget.
- **Perf gate k6**: `observabilidade/k6/seed-data-smoke.js` aplica thresholds p95<5s, p99<7s e `http_req_failed<0.02`, validando tambem presenca de RateLimit/Retry-After.
- **Telemetria fail-close**: falha de export OTEL/Sentry (`telemetry_unavailable`) reduz budget residual e bloqueia run quando repetida.
