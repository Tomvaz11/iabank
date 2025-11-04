# IABank — Fundação (F‑10)

Guia rápido para executar a suíte completa de validações localmente (frontend, backend, contratos e performance).

## Pré‑requisitos
- Node.js 20 e pnpm 9 (ver `package.json` → `packageManager`)
- Python 3.11 + Poetry (dev deps em `pyproject.toml`)
- k6 CLI (para testes de performance)
- Playwright (navegadores): `pnpm --filter @iabank/frontend-foundation exec playwright install --with-deps`

## Serviços (Postgres/Redis)
Você pode usar serviços locais ou subir via Docker Compose (porta alta para evitar conflitos):

```bash
FOUNDATION_STACK_POSTGRES_PORT=55432 \
FOUNDATION_STACK_REDIS_PORT=56379 \
  docker compose -f infra/docker-compose.foundation.yml up -d postgres redis
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

# Python / Poetry
poetry install --with dev

# Playwright browsers
pnpm --filter @iabank/frontend-foundation exec playwright install --with-deps
```

## Suíte completa (1 comando)
Executa: formatação, lint, typecheck, Storybook + cobertura Chromatic por tenant, testes unitários e E2E, Lighthouse, contratos (Spectral + diff + codegen), Pact, performance k6 (modo local), Ruff e Pytest com cobertura.

```bash
pnpm format && \
  pnpm lint && \
  pnpm typecheck && \
  pnpm --filter @iabank/frontend-foundation storybook:build && \
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
- Chromatic local: `pnpm --filter @iabank/frontend-foundation storybook:build && pnpm --filter @iabank/frontend-foundation chromatic:check -- --verbose`
- Contratos/API: `pnpm openapi && pnpm pact:verify`
- Performance: `pnpm perf:smoke:local`
- Backend: `poetry run ruff check . && poetry run pytest -q`

## Troubleshooting rápido
- Playwright: rode `pnpm --filter @iabank/frontend-foundation exec playwright install --with-deps` se faltar navegador.
- Postgres/Redis: ajuste portas em `infra/docker-compose.foundation.yml` via `FOUNDATION_STACK_POSTGRES_PORT` e `FOUNDATION_STACK_REDIS_PORT`.
- OTEL (k6): para publicar métricas, defina `OTEL_EXPORTER_OTLP_ENDPOINT` (ex.: `http://localhost:4318`).
