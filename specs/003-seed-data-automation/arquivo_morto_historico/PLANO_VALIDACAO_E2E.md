# Plano de Validação E2E — IABank Fundação (F‑10)

Este plano executa, end‑to‑end, tudo que está implementado até o momento: qualidade de código (FE/BE), testes (unit/E2E), contratos (OpenAPI/Pact), performance (k6/Lighthouse), segurança (SAST/SCA/DAST + pgcrypto), observabilidade (Prometheus/Grafana/OTEL), SBOM e checks auxiliares (complexidade, docs gate, threat model). As instruções assumem execução local com Docker.

## Objetivos
- Validar ponta‑a‑ponta frontend, backend, contratos e infraestrutura local de observabilidade.
- Reproduzir os gates essenciais do CI localmente, gerando evidências.
- Sinalizar claramente critérios de aceite e artefatos de saída por fase.

## Escopo e Origem (F‑10 — Fundação)
- Este plano cobre exclusivamente a Feature F‑10 (Fundação: FSD, Design System, Telemetria, Contratos e Observabilidade). Não há implementação das demais features F‑01…F‑09 neste repositório hoje.
- Artefatos de origem:
  - Índice geral: `specs/001-indice-features-template/spec.md`
  - Especificação da F‑10: `specs/002-f-10-fundacao/spec.md`
  - Plano/Tarefas/Pesquisa da F‑10: `specs/002-f-10-fundacao/plan.md`, `specs/002-f-10-fundacao/tasks.md`, `specs/002-f-10-fundacao/research.md`, `specs/002-f-10-fundacao/quickstart.md`
- Domínios e endpoints validados:
  - `GET /api/v1/tenants/{tenantId}/themes/current`
  - `POST /api/v1/tenants/{tenantId}/features/scaffold`
  - `GET /api/v1/tenant-metrics/{tenantId}/sc`
  - `GET /api/v1/design-system/stories`
- Frontend e CI relacionados:
  - Pacote: `@iabank/frontend-foundation` (frontend)
  - Workflow: `.github/workflows/frontend-foundation.yml`
  - Observabilidade: `infra/grafana/provisioning/**`, `infra/prometheus.local.yml`, `infra/docker-compose.foundation.yml`
- Fora do escopo atual: F‑01 (RBAC), F‑02 (KYC), F‑03 (Originação/Score/CET/IOF), F‑04 (Parcelas/Recebimentos), F‑05 (AP/Despesas), F‑06 (Cobrança/Renegociação), F‑07 (Painel Executivo), F‑08 (LGPD/WORM), F‑09 (Resiliência/Incidentes).
- Como verificar rapidamente:
  - `ls specs | rg '^003-|^004-|^005-'` (não deve retornar itens)
  - `rg -n 'F-0[1-9]|F-1[1-9]' specs/001-indice-features-template/spec.md` (F‑10 listado; demais como planejamento)

## Pré‑requisitos
- Node.js 20 + pnpm 9 (definidos em `package.json`).
- Python 3.11 + Poetry 1.8.3 (compatível com Docker/CI).
- Docker + Docker Compose.
- k6 CLI e Playwright (browsers): `pnpm --filter @iabank/frontend-foundation exec playwright install`.

- Chromatic (upload real opcional): exporte `CHROMATIC_PROJECT_TOKEN` antes da Fase 3. Sem o token, use apenas `chromatic:check`.

## Permissões/Recursos
- Rede externa habilitada (instalações npm/pnpm/Poetry, `docker pull`, `curl`).
- GitHub CLI (`gh`) autorizado e autenticado (consultar/listar/reexecutar workflows).
- Docker e Docker Compose permitidos para subir serviços locais.
- Ações destrutivas (ex.: `rm -rf`, `git reset --hard`, prune) exigem confirmação; demais usos não requerem aprovação adicional.
- Segredos não devem aparecer em logs/output. Para Chromatic:
  - Se `CHROMATIC_PROJECT_TOKEN` estiver definido no ambiente, executar upload real (`chromatic:ci`).
  - Caso contrário, usar apenas a verificação local de cobertura (`chromatic:check`).

## Fase 1 — Infra (Postgres/Redis/Backend)
1) Subir Postgres e Redis (portas altas para evitar conflito local):

```bash
FOUNDATION_STACK_POSTGRES_PORT=55432 \
FOUNDATION_STACK_REDIS_PORT=56379 \
  docker compose -f infra/docker-compose.foundation.yml up -d postgres redis
```

2) (Opcional) Subir backend via Compose (evita conflito com porta 8000 local):

```bash
FOUNDATION_STACK_BACKEND_PORT=58000 \
  docker compose -f infra/docker-compose.foundation.yml up -d backend
```

3) Variáveis para backend/Pytest em execução local (fora do Compose):

```bash
export FOUNDATION_DB_VENDOR=postgresql
export FOUNDATION_DB_HOST=127.0.0.1
export FOUNDATION_DB_PORT=55432
export FOUNDATION_DB_NAME=foundation
export FOUNDATION_DB_USER=foundation
export FOUNDATION_DB_PASSWORD=foundation
export FOUNDATION_PGCRYPTO_KEY=dev-only-pgcrypto-key
```

Critérios de aceite:
- Containers `postgres` e `redis` healthy.
- Backend responde `GET /metrics` sem 5xx (quando iniciado via Compose).

Artefatos: logs do `docker compose` (se necessário).

## Fase 2 — Instalação de Dependências

```bash
# Node / pnpm
pnpm install

# Python / Poetry
python -m pip install -U pip && pip install "poetry==1.8.3"
poetry install --with dev --sync --no-interaction --no-ansi

# Playwright browsers
pnpm --filter @iabank/frontend-foundation exec playwright install
```

Critérios de aceite: `node_modules` e ambiente Poetry prontos; `node -v`, `pnpm -v`, `poetry --version` compatíveis.

## Fase 3 — Qualidade e Testes (Frontend)

```bash
pnpm format && \
  pnpm lint && \
  pnpm typecheck && \
  pnpm test && \
  pnpm test:e2e
```

- Storybook e Chromatic (checagens locais):

```bash
pnpm --filter @iabank/frontend-foundation storybook:build && \
pnpm --filter @iabank/frontend-foundation storybook:test && \
pnpm --filter @iabank/frontend-foundation chromatic:check -- --verbose
```

- Chromatic (upload real — opcional, com token):

```bash
# Pré‑requisito: export CHROMATIC_PROJECT_TOKEN=<seu-token>
pnpm --filter @iabank/frontend-foundation storybook:build && \
pnpm --filter @iabank/frontend-foundation chromatic:ci
```

- Lighthouse budgets:

```bash
pnpm perf:lighthouse
```

Critérios de aceite:
- ESLint sem erros; TS sem erros.
- Vitest verde; cobertura de branches ≥ 85% (`frontend/coverage/coverage-summary.json`).
- Storybook Test Runner verde; Chromatic check OK local (sem quedas de cobertura do stories.json).
- Se token disponível: upload do Chromatic concluído com sucesso (usa `--exit-once-uploaded`/`--exit-zero-on-changes`).
- Lighthouse sem regressões críticas conforme orçamento.

Artefatos: `frontend/coverage/coverage-summary.json` e logs dos comandos.

## Fase 4 — Contratos (OpenAPI + Pact)

```bash
pnpm openapi && pnpm pact:verify
```

- OpenAPI: Spectral lint + diff + codegen (gera `frontend/src/shared/api/generated`).
- Pact: verificação dos contratos de consumidor (Vitest/Pact) do frontend.

Critérios de aceite: Spectral/diff sem quebras; codegen compila; Pact consumer tests verdes.

Artefatos: logs de `openapi:*`, `frontend/pacts/*` (se gerados).

## Fase 5 — Qualidade e Testes (Backend)

```bash
poetry run ruff check . && \
  poetry run pytest -q
```

- Inclui validações RLS/pgcrypto, serializadores e CSP via suíte de testes.
- Complexidade (Radon):

```bash
poetry run python scripts/ci/check_python_complexity.py
```

Critérios de aceite: Ruff sem findings; Pytest verde; complexidade cc ≤ 10 (ou conforme allowlist).

Artefatos: `artifacts/pytest/*` (se configurado), logs do teste e do gate de complexidade.

## Fase 6 — Performance (k6 + Alert Handler)

- Smoke local (Vite preview + k6):

```bash
pnpm perf:smoke:local
```

- Cenário mais forte (opcional):

```bash
FOUNDATION_PERF_VUS=50 pnpm perf:smoke:ci
```

Critérios de aceite:
- `artifacts/perf/k6-smoke.json` com `status` não “critical” em modo local.
- Publicação opcional da métrica `foundation_api_throughput` via OTEL se `OTEL_EXPORTER_OTLP_ENDPOINT` estiver definido.

Artefatos: `artifacts/perf/k6-smoke.json`.

## Fase 7 — Observabilidade Local (Prometheus, Grafana, OTEL)

1) Subir `otel-collector` e backend (além de Postgres/Redis já ativos):

```bash
docker compose -f infra/docker-compose.foundation.yml up -d backend otel-collector
```

2) Subir Prometheus (apontando para o backend do Compose):

```bash
docker run -d --name infra-prometheus --network infra_default -p 9090:9090 \
  -v "$PWD/infra/prometheus.local.yml:/etc/prometheus/prometheus.yml:ro" \
  prom/prometheus:v2.53.0
```

3) Subir Grafana com provisioning local:

```bash
docker run -d --name infra-grafana --network infra_default -p 3000:3000 \
  -e GF_AUTH_ANONYMOUS_ENABLED=true -e GF_AUTH_ANONYMOUS_ORG_ROLE=Admin \
  -v "$PWD/infra/grafana/provisioning:/etc/grafana/provisioning:ro" \
  grafana/grafana:10.4.5
```

4) Gerar tráfego e registrar SC‑001:

```bash
for i in $(seq 1 10); do curl -s -o /dev/null http://localhost:8000/metrics; done

TENANT=00000000-0000-0000-0000-000000000001
KEY=$(python3 - <<'PY'\nimport uuid; print(uuid.uuid4())\nPY
)

curl -s -X POST http://localhost:8000/api/v1/tenants/$TENANT/features/scaffold \
  -H 'Content-Type: application/json' \
  -H "X-Tenant-Id: $TENANT" \
  -H "Idempotency-Key: $KEY" \
  -d '{
    "featureSlug": "loan-tracking",
    "initiatedBy": "00000000-0000-4000-8000-000000000123",
    "slices": [
      { "slice": "app",   "files": [{"path":"frontend/src/app/loan-tracking/index.tsx",   "checksum": "4a7d..."}]},
      { "slice": "pages", "files": [{"path":"frontend/src/pages/loan-tracking/index.tsx", "checksum": "6b86..."}]}
    ],
    "lintCommitHash": "1234567890abcdef1234567890abcdef12345678",
    "scReferences": ["@SC-001", "@SC-003"],
    "durationMs": 1450,
    "metadata": {"cliVersion": "0.1.0"}
  }'

# (Opcional) Exercitar endpoints adicionais para ver métricas/headers
curl -s -H "X-Tenant-Id: tenant-alfa" http://localhost:8000/api/v1/tenant-metrics/tenant-alfa/sc > /dev/null
```

5) Enviar spans reais (frontend CLI):

```bash
pnpm --filter @iabank/frontend-foundation foundation:otel \
  --endpoint http://localhost:4318/v1/traces \
  --tenant tenant-alfa \
  --feature loan-tracking \
  --service frontend-foundation \
  --resource deployment.environment=local,service.namespace=iabank
```

Critérios de aceite:
- Prometheus target `up` e séries HTTP/latência p95 visíveis.
- Painel “IABank Foundation — Observabilidade Local” com gráficos populados (inclui séries SC‑001).
- Collector recebendo spans sem erros.

Artefatos: capturas do Grafana (opcional) e logs do Collector.

## Fase 8 — Segurança (SAST/SCA/DAST + pgcrypto)

```bash
# SAST (Semgrep)
bash scripts/security/run_sast.sh

# SCA Python (pip-audit + Safety)
poetry self add poetry-plugin-export || true
poetry run bash scripts/security/run_python_sca.sh all

# SCA Node (frontend)
pnpm audit:frontend || true

# DAST baseline (OWASP ZAP)
ZAP_BASELINE_TARGET=http://127.0.0.1:8000/metrics \
ZAP_SKIP_SERVER_START=1 \
  bash scripts/security/run_dast.sh

# Verificação de pgcrypto/EncryptedJSONField
poetry run python scripts/security/check_pgcrypto.py
bash scripts/security/check_pgcrypto.sh backend/
```

Critérios de aceite: sem High/Critical; DAST sem 5xx/achados críticos; pgcrypto validado.

Artefatos: `artifacts/python-sca/*`, logs do Semgrep/DAST.

## Fase 9 — Threat Model & Docs Gate

```bash
# Threat Model Lint
python scripts/security/threat_model_lint.py --release v1.0

# Docs Gate (drift e exigência de docs quando alterações impactantes)
node scripts/ci/check-docs-needed.js
```

Critérios de aceite: ambos OK sem erros.

## Fase 10 — SBOM e FinOps

```bash
# SBOM (frontend)
pnpm sbom:frontend

# FinOps (relatório local)
pnpm finops:report
```

Critérios de aceite: `sbom/frontend-foundation.json` gerado; relatório FinOps executa sem erro.

## Fase 11 — Pre‑commit (opcional, para alinhar ao CI)

```bash
poetry run pre-commit install || true
poetry run pre-commit run --all-files --show-diff-on-failure
```

Critério de aceite: hooks OK (Ruff/ESLint convergentes com passos anteriores).

## Fase 12 — CI via gh (opcional)

```bash
# Inspecionar últimos runs e required checks
gh run list --workflow "frontend-foundation.yml" --limit 10
```

Critério de aceite: jobs obrigatórios verdes (ver `docs/pipelines/ci-required-checks.md`).

---

## Checklist de Evidências
- Frontend: `frontend/coverage/coverage-summary.json`, logs (lint, typecheck, vitest, e2e, storybook, chromatic, lighthouse).
- Backend: logs (ruff, pytest), saída do gate de complexidade.
- Contratos: logs (Spectral, diff, codegen), Pact consumer tests.
- Performance: `artifacts/perf/k6-smoke.json`.
- Observabilidade: capturas do Grafana (opcional), logs do Collector, confirmação de targets Prometheus.
- Segurança: `artifacts/python-sca/*`, logs Semgrep/DAST, saída de `check_pgcrypto`.
- SBOM/FinOps: `sbom/frontend-foundation.json`, relatório FinOps.
- Threat Model e Docs Gate: saídas dos scripts com status OK.

## Notas
- Chromatic: o plano usa `chromatic:check` (cobertura local). Para upload real, defina `CHROMATIC_PROJECT_TOKEN` e use `chromatic:ci` se desejar.
- Performance local: thresholds são brandos por hardware. Para validação “hard”, use `FOUNDATION_PERF_VUS=50 pnpm perf:smoke:ci`.
- Terraform/OPA: não há IaC Terraform versionado neste repo; validações de política ficam fora do escopo local por ora.
