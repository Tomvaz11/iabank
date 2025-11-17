# IABank — Fundação (F‑10)

## Índice
- [Pré‑requisitos](#pré‑requisitos)
- [Serviços (Postgres/Redis)](#serviços-postgresredis)
- [Instalação](#instalação)
- [Suíte completa (1 comando)](#suíte-completa-1-comando)
- [Notas](#notas)
- [TDD & Evidências no PR](#tdd--evidências-no-pr)
- [Complexidade (Radon)](#complexidade-radon)
- [Execução por fases (opcional)](#execução-por-fases-opcional)
- [Observabilidade local (Prometheus, Grafana, OTEL)](#observabilidade-local-prometheus-grafana-otel)
- [Troubleshooting rápido](#troubleshooting-rápido)
- [Contribuição](#contribuição)

Guia rápido para executar a suíte completa de validações localmente (frontend, backend, contratos e performance).

## Pré‑requisitos
- Node.js 20 e pnpm 9 (ver `package.json` → `packageManager`)
- Python 3.11 + Poetry 1.8.3 (alinhado a CI/Docker)
- k6 CLI (para testes de performance)
 - Playwright (navegadores): `pnpm --filter @iabank/frontend-foundation exec playwright install`

## Serviços (Postgres/Redis)
Você pode usar serviços locais ou subir via Docker Compose (porta alta para evitar conflitos):

```bash
FOUNDATION_STACK_POSTGRES_PORT=55432 \
FOUNDATION_STACK_REDIS_PORT=56379 \
  docker compose -f infra/docker-compose.foundation.yml up -d postgres redis
```

Para evitar conflito com um serviço local na porta 8000, o backend no Compose expõe a variável `FOUNDATION_STACK_BACKEND_PORT`:

```bash
FOUNDATION_STACK_BACKEND_PORT=58000 \
  docker compose -f infra/docker-compose.foundation.yml up -d backend
```

As variáveis de ambiente abaixo serão usadas pelo pytest quando executado localmente:

```bash
export FOUNDATION_DB_VENDOR=postgresql
export FOUNDATION_DB_HOST=127.0.0.1
export FOUNDATION_DB_PORT=55432
export FOUNDATION_DB_NAME=foundation
export FOUNDATION_DB_USER=foundation
export FOUNDATION_DB_PASSWORD=foundation
```

## Instalação
```bash
# Node / pnpm
pnpm install

# Python / Poetry (pin 1.8.3 e instalação sem recriar lock)
python -m pip install -U pip && pip install "poetry==1.8.3"
poetry install --with dev --sync --no-interaction --no-ansi

# Playwright browsers
pnpm --filter @iabank/frontend-foundation exec playwright install
```

## Suíte completa (1 comando)
Executa: formatação, lint, typecheck, Storybook + teste de histórias (Storybook Test Runner) + cobertura Chromatic por tenant, testes unitários e E2E, Lighthouse, contratos (Spectral + diff + codegen), Pact, performance k6 (modo local), Ruff e Pytest com cobertura.

```bash
pnpm format && \
  pnpm lint && \
  pnpm typecheck && \
  pnpm --filter @iabank/frontend-foundation storybook:build && \
  pnpm --filter @iabank/frontend-foundation storybook:test && \
  pnpm --filter @iabank/frontend-foundation chromatic:check -- --verbose && \
  pnpm test && \
  pnpm test:e2e && \
  pnpm perf:lighthouse && \
  pnpm perf:smoke:local && \
  pnpm openapi && \
  pnpm pact:verify && \
  poetry run ruff check . && \
  FOUNDATION_DB_VENDOR=postgresql \
  FOUNDATION_DB_HOST=127.0.0.1 \
  FOUNDATION_DB_PORT=55432 \
  FOUNDATION_DB_NAME=foundation \
  FOUNDATION_DB_USER=foundation \
  FOUNDATION_DB_PASSWORD=foundation \
  poetry run pytest -q
```

Notas:
- Performance (k6) em modo local usa `FOUNDATION_PERF_VUS=1` por padrão e pode sinalizar status `critical` apenas por throughput. Para um OK completo, use algo como `FOUNDATION_PERF_VUS=50 pnpm perf:smoke:ci` ou ajuste `FOUNDATION_PERF_THROUGHPUT_CRITICAL`.
- A cobertura visual (Chromatic) requer build prévio do Storybook; o comando acima já executa o build.

## TDD & Evidências no PR
- Siga “vermelho → verde”: registre no PR os commits (ou links de run) do estado vermelho (falha esperada do teste) e do estado verde (após a implementação).
- Para casos de exceção (ajustes de CI/docs/hotfix infra), documente a justificativa no PR.

## Complexidade (Radon)
- Gate no CI: `scripts/ci/check_python_complexity.py` (limite cc ≤ 10; allowlist em `scripts/ci/complexity_allowlist.json`).
- Execução local: `poetry run python scripts/ci/check_python_complexity.py`.

## Execução por fases (opcional)
- Frontend: `pnpm format && pnpm lint && pnpm typecheck && pnpm test && pnpm test:e2e && pnpm perf:lighthouse`
- Storybook Test Runner: `pnpm --filter @iabank/frontend-foundation storybook:test`
- Chromatic local: `pnpm --filter @iabank/frontend-foundation storybook:build && pnpm --filter @iabank/frontend-foundation chromatic:check -- --verbose`
- Contratos/API: `pnpm openapi && pnpm pact:verify`
  - Codegen (alternativo/spike): `pnpm openapi:generate:next` gera cliente paralelo em `frontend/src/shared/api/generated-next` via `@hey-api/openapi-ts` (não substitui o atual).
- Performance: `pnpm perf:smoke:local`
- Backend: `poetry run ruff check . && poetry run pytest -q`
- Segurança:
  - SAST: `bash scripts/security/run_sast.sh`
  - SCA (Python):
    - Instale o plugin de export do Poetry (uma vez): `poetry self add poetry-plugin-export`
    - Exporte deps e audite via pip-audit:
      - `poetry export --format=requirements.txt --with dev --without-hashes -o artifacts/security/requirements.txt`
      - `pip-audit -r artifacts/security/requirements.txt`
    - Alternativamente, use o wrapper: `poetry run bash scripts/security/run_python_sca.sh all`
    - Nota (Poetry/Export): se o comando `poetry export` não existir (instalações via distro/snap podem não carregar plugins), alinhe-se à versão utilizada no CI e instale o plugin de export compatível. Consulte `.github/workflows/frontend-foundation.yml` e `docs/pipelines/ci-required-checks.md`.
  - DAST (OWASP ZAP baseline):
    - Se o backend via Compose já estiver ativo: `ZAP_BASELINE_TARGET=http://127.0.0.1:8000/metrics ZAP_SKIP_SERVER_START=1 bash scripts/security/run_dast.sh`
    - Caso contrário, o script aplicará migrações e iniciará `runserver` temporariamente (alvo padrão: `/metrics`).

Notas Lighthouse:
- Para execuções locais mais estáveis, use warmup e rodadas extras: `LIGHTHOUSE_RUNS=3 LIGHTHOUSE_WARMUP_DELAY_MS=8000 pnpm --filter @iabank/frontend-foundation test:lighthouse`.

## Observabilidade local (Prometheus, Grafana, OTEL)
Este passo valida “de ponta a ponta” as métricas (Prometheus/Grafana) e os traces (OTEL Collector) localmente.

1) Subir backend e OTEL Collector (além de Postgres/Redis já ativos):

```bash
docker compose -f infra/docker-compose.foundation.yml up -d backend otel-collector
```

2) Subir Prometheus apontando para o backend:

```bash
# Usa a rede do docker-compose (infra_default) e a config local
docker run -d --name infra-prometheus --network infra_default -p 9090:9090 \
  -v "$PWD/infra/prometheus.local.yml:/etc/prometheus/prometheus.yml:ro" \
  prom/prometheus:v2.53.0

# Verifique targets (deve aparecer health: up)
curl -s http://localhost:9090/api/v1/targets | jq .  # opcional
```

3) Subir Grafana com datasource e dashboard provisionados:

```bash
docker run -d --name infra-grafana --network infra_default -p 3000:3000 \
  -e GF_AUTH_ANONYMOUS_ENABLED=true -e GF_AUTH_ANONYMOUS_ORG_ROLE=Admin \
  -v "$PWD/infra/grafana/provisioning:/etc/grafana/provisioning:ro" \
  grafana/grafana:10.4.5

# Acesse http://localhost:3000 e procure o painel
# “IABank Foundation — Observabilidade Local” (datasource Prometheus já é default)
```

4) Gerar tráfego e uma métrica de negócio (SC‑001) para popular o painel:

```bash
# Requisições ao /metrics (popular séries HTTP/latência)
for i in $(seq 1 10); do curl -s -o /dev/null http://localhost:8000/metrics; done

# Registrar um scaffolding (SC‑001) para gerar buckets/sum/count do histograma
TENANT=00000000-0000-0000-0000-000000000001  # tenant-alfa (semente padrão)
KEY=$(python3 - <<'PY'
import uuid; print(uuid.uuid4())
PY
)
curl -s -X POST http://localhost:8000/api/v1/tenants/$TENANT/features/scaffold \
  -H 'Content-Type: application/json' \
  -H "X-Tenant-Id: $TENANT" \
  -H "Idempotency-Key: $KEY" \
  -d '{
    "featureSlug": "loan-tracking",
    "initiatedBy": "00000000-0000-4000-8000-000000000123",
    "slices": [
      { "slice": "app",   "files": [{"path":"frontend/src/app/loan-tracking/index.tsx",   "checksum": "4a7d1ed414474e4033ac29ccb8653d9b4a7d1ed414474e4033ac29ccb8653d9b"}]},
      { "slice": "pages", "files": [{"path":"frontend/src/pages/loan-tracking/index.tsx", "checksum": "6b86b273ff34fce19d6b804eff5a3f5746e0f2c6313be24d09aef7b54afc8cdd"}]}
    ],
    "lintCommitHash": "1234567890abcdef1234567890abcdef12345678",
    "scReferences": ["@SC-001", "@SC-003"],
    "durationMs": 1450,
    "metadata": {"cliVersion": "0.1.0"}
  }'
```

5) Verificar o painel no Grafana
- HTTP req/s por método, erros 5xx (%) e latência p95 devem começar a aparecer.
- O gráfico “SC‑001 — Duração média (min) por feature” usa as séries `sc_001_scaffolding_minutes_{sum,count}`.

6) Verificar OTEL Collector recebendo spans reais

```bash
pnpm --filter @iabank/frontend-foundation foundation:otel \
  --endpoint http://localhost:4318/v1/traces \
  --tenant tenant-alfa \
  --feature loan-tracking \
  --service frontend-foundation \
  --resource deployment.environment=local,service.namespace=iabank
```

Você verá um JSON resumo (com chaves mascaradas) e o Collector registrará o recebimento do span nos logs.

7) Encerrar serviços locais (opcional)

```bash
docker compose -f infra/docker-compose.foundation.yml down
docker rm -f infra-prometheus infra-grafana
```

8) Atalho (Demo local)

Para visualizar rapidamente a métrica SC‑001 sem depender de múltiplos eventos e sem alterar o painel oficial, use o painel “Demo” e o script de seed:

```bash
# (com backend + prometheus + grafana ativos)
bash scripts/observabilidade/seed_sc001.sh loan-tracking-demo 1

# Abra no Grafana: IABank → "IABank Foundation — Observabilidade Local (Demo)"
# O gráfico "SC‑001 — Duração média (min) [Demo]" mostra o valor médio
```

## Troubleshooting rápido
- Playwright: rode `pnpm --filter @iabank/frontend-foundation exec playwright install` se faltar navegador.
- Postgres/Redis: ajuste portas em `infra/docker-compose.foundation.yml` via `FOUNDATION_STACK_POSTGRES_PORT` e `FOUNDATION_STACK_REDIS_PORT`.
- OTEL (k6): para publicar métricas, defina `OTEL_EXPORTER_OTLP_ENDPOINT` (ex.: `http://localhost:4318`).
- Grafana: se o painel não aparecer, reinicie o container para reprocessar o provisioning (`docker restart infra-grafana`) e valide os volumes montados em `infra/grafana/provisioning`.
- Prometheus: se o target não estiver UP, confirme a rede `infra_default` e o endpoint `backend:8000/metrics` na `infra/prometheus.local.yml`.

## Contribuição
- Fluxo Git, Padrão de branches, PRs e checks: veja `CONTRIBUTING.md`.
- Runbooks úteis:
  - Outage (Chromatic/Lighthouse/Axe): `docs/runbooks/frontend-outage.md`
  - Renovate Validation: `docs/runbooks/renovate-validation.md`
  - Vault/PII: `docs/runbooks/seguranca-pii-vault.md`
  
