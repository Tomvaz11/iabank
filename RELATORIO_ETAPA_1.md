# Relatório de Validação E2E — Etapa 1 (Fases 1–5)

Status: CONCLUÍDA

## Metadados
- Repositório: iabank
- Branch: main
- Commit: ca5901a
- Data/Hora: 2025-11-16T13:44:29-03:00
- Ferramentas: Node v20.17.0; pnpm 9.12.2; Poetry (version 2.2.1)

## Síntese dos Resultados
- Infra ok: Postgres e Redis "healthy"; backend via Compose respondeu `GET /metrics` com 200.
- Frontend ok: lint, typecheck, unit/E2E, Storybook Test Runner e Lighthouse passaram; Chromatic em check local.
- Contratos ok: Spectral/diff sem quebras, codegen gerado, Pact consumer tests verdes.
- Backend ok: Ruff/pytest verdes; complexidade ciclomática dentro do limite (<= 10).

---

## Fase 1 — Infra (Postgres/Redis/Backend)
- Comandos executados:
  - `FOUNDATION_STACK_POSTGRES_PORT=55432 FOUNDATION_STACK_REDIS_PORT=56380 docker compose -f infra/docker-compose.foundation.yml up -d postgres redis`
  - Health: `docker compose -f infra/docker-compose.foundation.yml ps`
  - Verificação backend: `curl -fsS http://127.0.0.1:58000/metrics` → 200
- Observações:
  - Porta 56379 estava ocupada; Redis exposto em 56380.
- Resultado:
  - `postgres` e `redis` healthy; backend acessível em `http://127.0.0.1:58000/metrics`.

## Fase 2 — Instalação de Dependências
- Comandos executados:
  - `pnpm install`
  - `poetry install --with dev --sync --no-interaction --no-ansi`
  - `pnpm --filter @iabank/frontend-foundation exec playwright install`
- Resultado:
  - Ambiente Node/pnpm pronto; ambiente Poetry instalado; Playwright browsers instalados.

## Fase 3 — Qualidade e Testes (Frontend)
- Comandos executados:
  - `pnpm format && pnpm lint && pnpm typecheck && pnpm test && pnpm test:e2e`
  - `pnpm --filter @iabank/frontend-foundation storybook:build && pnpm --filter @iabank/frontend-foundation storybook:test`
  - `pnpm --filter @iabank/frontend-foundation chromatic:check -- --verbose`
  - `pnpm perf:lighthouse`
- Resultados principais:
  - ESLint/TS: sem erros.
  - Vitest: verde. Cobertura total (json-summary):
    - Lines 91.91%; Statements 91.91%; Functions 87.23%; Branches 85.95%.
    - Arquivo: `frontend/coverage/coverage-summary.json`.
  - Storybook Test Runner: verde. Chromatic (check local): cobertura de stories ≥ 95% por tenant (100% reportado).
  - Lighthouse budgets: respeitados (teste passou).
- Observação de segurança:
  - `CHROMATIC_PROJECT_TOKEN` não exportado localmente (sem upload). Secret presente no repositório GitHub para uso em CI.

## Fase 4 — Contratos (OpenAPI + Pact)
- Comandos executados:
  - `pnpm openapi` (Spectral lint, diff, codegen)
  - `pnpm pact:verify`
- Resultados:
  - Spectral/diff: sem quebras.
  - Codegen: gerado em `frontend/src/shared/api/generated` (compila).
  - Pact consumer tests: verdes.

## Fase 5 — Qualidade e Testes (Backend)
- Comandos executados:
  - `poetry run ruff check .`
  - `poetry run pytest -q`
  - `poetry run python scripts/ci/check_python_complexity.py`
- Resultados:
  - Ruff: All checks passed.
  - Pytest: verde (saída padrão mostra cobertura por arquivo; sem falhas).
  - Complexidade: "Complexidade ciclomática dentro do limite (<=10)".

## Artefatos
- Cobertura frontend: `frontend/coverage/coverage-summary.json`
- Storybook estático: `frontend/storybook-static/iframe.html`
- OpenAPI codegen: `frontend/src/shared/api/generated/index.ts`
- Pacts: `contracts/pacts/`
- Script do gate de complexidade: `scripts/ci/check_python_complexity.py`

## Considerações
- Uso de Chromatic: somente checagem local; upload deve ocorrer no CI (secret configurado no repositório GitHub).
- Serviços locais expostos em portas: Postgres 55432; Redis 56380; Backend 58000.

