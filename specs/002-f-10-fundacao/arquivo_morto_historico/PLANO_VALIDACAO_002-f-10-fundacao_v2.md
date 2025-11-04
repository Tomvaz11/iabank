# Plano de Validação Exaustiva — 002-f-10-fundação (v2)

## Objetivos
- Revalidar, de ponta a ponta, todas as entregas da feature `002-f-10-fundacao` com ênfase em “zero warnings” e “zero gaps”.
- Executar testes reais e verificações práticas (backend, frontend, contratos, E2E, performance, segurança, observabilidade) e registrar evidências reproduzíveis.
- Produzir artefatos e um relatório consolidado em `artifacts/validacao-002-f-10-v2/`.

## Escopo Coberto
- Frontend (`@iabank/frontend-foundation`): lint/format, typecheck, build, testes unitários (Vitest), E2E (Playwright), Storybook + Chromatic check, Lighthouse com budgets, TanStack Query + Zustand, telemetria (OTEL) e CLIs de fundação.
- Backend (Django 4.2): migrações, RLS/pgcrypto, políticas de segurança (CSP/Trusted Types), endpoints `foundation`, pytest + cobertura, ruff, bandit, radon, métricas Prometheus.
- Contratos: OpenAPI (Spectral + diff + codegen) e Pact (interações definidas na fundação).
- Observabilidade e operações: emissão de spans/metrics (OTEL), dashboards SC-001..SC-005, runbooks, FinOps, guardas de indisponibilidade no CI.
- Segurança e conformidade: SAST (Semgrep), SCA (pnpm audit / safety/pip-audit), SBOM (CycloneDX), DAST baseline, PII masking.

## Princípios de Execução
- “Sem warnings”: tratar warnings relevantes como falhas. Onde cabível, rodar com sinalizadores de warnings como erro (ex.: `pytest -W error`). Se inviável por toolchain, evidenciar e justificar no relatório.
- Idempotência: cada etapa deve poder ser reexecutada; limpar artefatos antigos antes de iniciar.
- Evidências: toda execução salva logs/relatórios sob `artifacts/validacao-002-f-10-v2/` com prefixos numerados para fácil rastreio.
- Sem alterações funcionais: somente correções necessárias para eliminar warns/buracos. Qualquer ajuste estrutural deve ser registrado nos aprendizados/follow-ups.

## Pré‑requisitos e Ambiente
- Ferramentas: Node.js 20.x, pnpm 9.x, Python 3.11, Poetry, Docker + Compose, Git, k6, Playwright browsers.
- Variáveis úteis (local): `FOUNDATION_DB_*`, `FOUNDATION_PGCRYPTO_KEY`, `TENANT_DEFAULT`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, `OTEL_RESOURCE_ATTRIBUTES`.
- Alternativas de orquestração: `docker compose -f infra/docker-compose.foundation.yml` ou `scripts/dev/foundation-stack.sh`.

## Estrutura de Artefatos (v2)
- Diretório: `artifacts/validacao-002-f-10-v2/`
  - `0-ambiente/` — versões, diagnóstico de Docker, espaço em disco.
  - `1-setup/` — instalações (pnpm/poetry), locks, checksums e `git status` inicial.
  - `2-backend/` — `ruff`, `bandit`, `radon`, `pytest` (+ cobertura), migrações e checks de deploy.
  - `3-frontend/` — `lint`, `typecheck`, `vitest` (+ cobertura), build, Storybook, Playwright (E2E) e Lighthouse.
  - `4-contratos/` — `spectral`, `openapi-diff`, `openapi-typescript-codegen`, Pact.
  - `5-perf-obs/` — k6 smoke, evidências LH, export de spans/metrics (OTEL), verificações de mascaramento de PII.
  - `6-seguranca/` — SCA/SAST/DAST, SBOM e relatórios correlatos.
  - `resumo.md` e `relatorio-final.md` — síntese e conclusões v2.

## Critérios de Aceite (v2)
- Lint/typecheck sem warnings/erros; builds concluídos.
- Cobertura ≥ 85% (frontend e backend) e complexidade ≤ 10 (radon/ESLint).
- OpenAPI lint/sync/diff OK; codegen atualizado; Pact verde.
- E2E e Lighthouse dentro dos budgets (LCP ≤ 2.5s, TTI ≤ 3.0s, CLS ≤ 0.1).
- Segurança sem High/Critical (SAST/SCA/DAST); SBOM gerada; CSP/Trusted Types efetivos; RLS/pgcrypto validados.
- Observabilidade com spans/métricas esperadas, sem PII não mascarada.

## Sequência Detalhada de Validação (v2)

### 0. Limpeza/Preparação
1) Criar pasta v2: `mkdir -p artifacts/validacao-002-f-10-v2/{0-ambiente,1-setup,2-backend,3-frontend,4-contratos,5-perf-obs,6-seguranca}`.
2) Encerrar stack anterior (se houver): `docker compose -f infra/docker-compose.foundation.yml down -v || true` (log em `0-ambiente/compose-down.log`).

### 1. Diagnóstico do Ambiente
- `node -v`, `pnpm -v`, `python --version`, `poetry --version`, `docker compose version`, `docker info`, `df -h` → `0-ambiente/diagnostico.log`.
- Validar `.nvmrc`, `.tool-versions`, engines do `package.json` e `pyproject.toml` para consistência de versões.

### 2. Instalação/Setup
- Node/JS:
  - `pnpm -w install` → `1-setup/pnpm-install.log`.
  - `pnpm -w dedupe` (opcional) → `1-setup/pnpm-dedupe.log`.
- Python:
  - `poetry install --with dev` → `1-setup/poetry-install.log`.
- Sanidade do repo: `git status`, `pnpm -w list -r`, `poetry show` → `1-setup/sumario.log`.

### 3. Backend (lint, complexidade, testes)
- Lint/estáticos: `poetry run ruff check backend` → `2-backend/ruff.log`.
- SAST/complexidade: `poetry run bandit -r backend/apps -ll` → `2-backend/bandit.log`; `poetry run radon cc backend/apps -nc -s` → `2-backend/radon.log`.
- Migrações e checks: `poetry run python backend/manage.py migrate` e `poetry run python backend/manage.py check --deploy` → `2-backend/django-checks.log`.
- Testes com cobertura (warnings como erro): `pytest -W error` → `2-backend/pytest.log`.
- Métricas endpoint: `pytest -k metrics_endpoint` para confirmar `/metrics` Prometheus.

### 4. Frontend (lint, typecheck, testes, build)
- Lint: `pnpm lint` → `3-frontend/eslint.log` (sem warnings).
- Typecheck: `pnpm typecheck` → `3-frontend/typecheck.log`.
- Unit tests + cobertura: `pnpm test:coverage` → `3-frontend/vitest.log`.
- Build: `pnpm build:frontend` → `3-frontend/build.log`.
- Storybook: `pnpm --filter @iabank/frontend-foundation storybook:build` e `storybook:test` → `3-frontend/storybook.log`.

### 5. E2E e Performance
- Playwright E2E: `pnpm test:e2e` (instalar browsers se necessário: `pnpm exec playwright install --with-deps`) → `3-frontend/e2e.log`.
- Lighthouse budgets: `pnpm perf:lighthouse` → `5-perf-obs/lighthouse.log` (+ relatórios gerados).
- k6 smoke: `pnpm perf:smoke:ci` → `5-perf-obs/k6-smoke.log` e `artifacts/k6-smoke.json`.
 - k6 smoke (CI): `pnpm perf:smoke:ci` → `5-perf-obs/k6-smoke.log` e `artifacts/k6-smoke.json`.
 - k6 smoke (local): `pnpm perf:smoke:local` (thresholds ajustados para dev) — pode usar `FOUNDATION_PERF_PORT=50xxx` para porta alta.

### 6. Contratos (OpenAPI + Pact)
- Lint: `pnpm openapi:lint` → `4-contratos/spectral.log`.
- Diff: `pnpm openapi:diff` → `4-contratos/openapi-diff.log`.
- Codegen: `pnpm openapi:generate` → `4-contratos/codegen.log` (verificar diffs em `frontend/src/shared/api/generated`).
- Pact verify: `pnpm pact:verify` → `4-contratos/pact.log`.

### 7. Observabilidade e Telemetria
- OTEL verificação ativa: `pnpm --filter @iabank/frontend-foundation foundation:otel` → `5-perf-obs/otel-verify.log` (conferir baggage e mascaramento).
- Confirmar recebimento no collector (se stack local ativa) e logs do backend para `trace_id` correlacionado.

### 8. Segurança e Conformidade
- SCA Node: `pnpm --dir frontend audit --prod --audit-level=high --json` → `6-seguranca/pnpm-audit.json` (sem High/Critical).
- SCA Python: `poetry run pip-audit -r poetry.lock || poetry run safety check` → `6-seguranca/pip-audit.log`.
- SAST: `semgrep --config auto` (ou política do repo) → `6-seguranca/semgrep.log`.
- DAST baseline (local): ZAP contra serviços da stack (se aplicável) → `6-seguranca/zap-baseline.log`.
- SBOM: `pnpm sbom:frontend` → `frontend/sbom/frontend-foundation.json` e cópia em `6-seguranca/sbom-frontend.json`.

### 9. Revisões Cruzadas e Documentação
- Confirmar coerência entre `specs/002-f-10-fundacao/spec.md`, `plan.md`, `tasks.md` (todos os [X] com evidências correspondentes) → `resumo.md`.
- Validar runbooks (`docs/runbooks/frontend-foundation.md`), ADR (`docs/adr/adr-perf-front.md`) e LGPD (`docs/lgpd/rls-evidence.md`) com as evidências coletadas.
- Conferir harmonização `observabilidade/` vs `observability/` (T113) via busca: `rg "observability"` e registrar achados.

### 10. Saída e Consolidação
- `git status` deve estar limpo; gerar `resumo.md` e `relatorio-final.md` com:
  - Métricas‑chave (cobertura, budgets, findings de segurança).
  - Lista de comandos executados e onde estão os logs/relatórios.
  - Pendências e recomendações (se existirem) — porém alvo é zero pendências.

## Considerações e Riscos
- Dependências de rede (instalação de pacotes/browsers, pulls Docker) podem exigir aprovação prévia e podem variar conforme caching local.
- E2E/Lighthouse exigem recursos de CPU/RAM/Chrome; rodar isoladamente se necessário.
- Se ZAP não estiver disponível localmente, registrar a limitação e cobrir com validações alternativas temporárias.

## Próximos Passos (execução)
1) Rodar “1. Diagnóstico do Ambiente” e “2. Instalação/Setup”.
2) Prosseguir com “3. Backend” → “4. Frontend” → “5. E2E e Performance”.
3) Finalizar com “6. Contratos”, “7. Observabilidade” e “8. Segurança”.
4) Consolidar o relatório final v2.
