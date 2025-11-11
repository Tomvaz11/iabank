# Plano de Validação Exaustiva — 002-f-10-fundação

## Objetivos
- Garantir que todas as entregas da feature 002-f-10-fundação estejam funcionais, íntegra e operacionalmente alinhadas ao blueprint.
- Executar testes, lint, contratos, fluxos CLI e validações de observabilidade sem warnings ou falhas.
- Registrar evidências reproduzíveis de cada verificação em `artifacts/validacao-002-f-10/`.

## Escopo Coberto
- Frontend (`@iabank/frontend-foundation`: lint, build, tests unitários, e2e, Storybook/Chromatic, Lighthouse, k6, OTEL, Zustand/TanStack Query).
- Backend (Django: migrações, RLS, pgcrypto, API `foundation`, políticas de segurança, pytest, ruff, bandit, radon).
- Contratos e integração (OpenAPI, Pact, scripts de diff e geração).
- Observabilidade e operações (OTEL, dashboards SC-001..SC-005, runbooks, finops, scripts de outage).
- Segurança (CSP, Trusted Types, mascaramento PII, scanners).
- Ferramentas auxiliares e CLIs (`foundation:scaffold`, `foundation:tokens`, `foundation:otel`, `finops:report`, `ci:outage`).

## Organização Geral
- Criar o diretório `artifacts/validacao-002-f-10/` para capturar saídas relevantes (logs das execuções, relatórios JSON, prints de cobertura, export de dashboards).
- Padronizar logs de comandos com `tee artifacts/validacao-002-f-10/<etapa>.log`.
- Caso algum comando dependa de segredos, usar variáveis `FOUNDATION_*` conforme `specs/002-f-10-fundacao/quickstart.md` e registrar no log se foram mockadas.
- Toda falha deve gerar issue interna ou anotação em `artifacts/validacao-002-f-10/riscos.md` até correção.

## Protocolo de Execução (Codex CLI)
- Aprovação/elevação: instalar dependências (rede), Playwright, Docker/Compose e quaisquer pulls de imagens exigem aprovação. Solicitarei antes de cada bloco.
- Captura de evidências: todo comando relevante roda com `| tee artifacts/validacao-002-f-10/<ordem>-<nome>.log` e arquivos JSON/HTML são guardados no mesmo diretório.
- Ordem macro de execução (comandos canônicos do monorepo):
  1. `pnpm install` e `poetry install --with dev`
  2. `docker compose -f infra/docker-compose.foundation.yml up -d`
  3. Backend: `poetry run ruff check backend`, `poetry run bandit -r backend/apps -ll`, `poetry run radon cc backend/apps -nc -s`, `pytest`
  4. Frontend: `pnpm lint`, `pnpm typecheck`, `pnpm test:coverage`, `pnpm test:e2e`, `pnpm storybook:build && pnpm storybook:test`
  5. Contratos: `pnpm openapi:lint`, `pnpm openapi:diff`, `pnpm openapi:generate`, `pnpm pact:verify`
  6. Performance/UX: `pnpm perf:lighthouse`, `pnpm perf:smoke:ci`
  7. Observabilidade/FinOps/CI: `pnpm finops:report`, `pnpm ci:outage`
- Variáveis recomendadas para local: `FOUNDATION_DB_*`, `FOUNDATION_PGCRYPTO_KEY`, `TENANT_DEFAULT`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, `OTEL_RESOURCE_ATTRIBUTES`.
- Limpeza antes de iniciar: `docker compose -f infra/docker-compose.foundation.yml down -v || true` e remoção do diretório `artifacts/validacao-002-f-10/` anterior.

## Mapeamento de Cobertura ↔ Tasks (@specs)
- Fase 0 (T001, T007–T008, T090–T091): validada em Seções 3, 8 e 10 (linters, contratos, Pact, RLS).
- Fase 1 (T009–T014, T109, T092): Seções 2, 3 e 5 (setup, lint, testes básicos e CI refletidos nos testes de workflows).
- Fundamentos (T015–T024): Seções 3–7 e 11 (tenancy/query, tokens, OTEL base, migrações/RLS, headers de segurança).
- US1/US2/US3 (T025–T060, T079, T099): Seções 5–9 e 11 (CLI scaffold/tokens/otel, endpoints e métricas de sucesso, CSP/Trusted Types, verificação de telemetria).
- Final (T061–T113): Seções 11–12–13 e 14–15 (dashboards, runbooks, performance budgets, segurança/SBOM/SCA/SAST/DAST, ADR/Threat Model, gates de cobertura/complexidade).

## Critérios de Aceite Globais
- Zero erros e zero warnings relevantes em: `pnpm lint`, `pnpm typecheck`, `pytest` (inclui cobertura), `ruff`, `bandit` (sem High), `radon` (complexidade ≤ 10), Spectral (sem violations) e `openapi-diff` (sem breaking inesperado).
- Cobertura mínima: frontend e backend ≥ 85% (gate já definido: `pytest.ini` e `frontend` via `vitest --coverage`).
- Pact: todas interações `pact:verify` passadas; arquivos de pact atualizados/ou consistentes.
- RLS/pgcrypto: testes e checagens manuais garantem rejeição sem `X-Tenant-Id` e segregação/cripto ok.
- Segurança: CSP/Trusted Types efetivos, `pnpm audit:frontend` sem High/Critical, SAST/DAST sem High, SBOM gerada.
- Performance/UX: budgets Lighthouse atendidos (LCP ≤ 2.5s, TTI ≤ 3.0s, CLS ≤ 0.1). k6 smoke exporta métrica `foundation_api_throughput` em OTEL.
- Observabilidade: spans emitidos com baggage de `tenant_id`, PII mascarada; FinOps report gerado.
- Repositório limpo ao final: `git status` sem diffs.

## Sequência Detalhada de Validação

### 1. Preparação de Ambiente
- [ ] Confirmar versões: `node -v`, `pnpm -v`, `python --version`, `poetry --version`, `docker compose version` (`artifacts/.../0-ambiente.log`).
- [ ] Validar disponibilidade de Docker e espaço em disco (`docker info`, `df -h`).
- [ ] Carregar segredos necessários (Vault ou mocks locais) e exportar `FOUNDATION_*`, `OTEL_*`.
- [ ] Limpar resíduos anteriores: `docker compose -f infra/docker-compose.foundation.yml down -v`, excluir `artifacts/validacao-002-f-10/` antigo.

### 2. Provisionamento Inicial
- [ ] Instalar dependências: `pnpm install` e `poetry install --with dev`.
- [ ] Provisionar stack: `docker compose -f infra/docker-compose.foundation.yml up -d`.
- [ ] Validar serviços: `docker compose -f infra/docker-compose.foundation.yml ps`, logs do backend/frontend (`docker compose ... logs backend`).
- [ ] Aplicar migrações manualmente se necessário: `docker compose exec backend python manage.py migrate`.
- [ ] Rodar `docker compose exec backend python manage.py check --deploy` e registrar saída.

### 3. Qualidade Backend
- [ ] `poetry run ruff check backend` (sem warnings).
- [ ] `poetry run bandit -r backend/apps -ll`.
- [ ] `poetry run radon cc backend/apps -nc -s` e `radon mi` para manter complexidade aceitável.
- [ ] `poetry run pytest` com `--cov` (verificar cobertura ≥85%, sem testes pendentes).
- [ ] Rodar especificamente `poetry run pytest backend/apps/tenancy/tests/test_rls_enforcement.py -vv` e analisar mensagens RLS.

### 4. Banco e RLS
- [ ] Via psql: validar políticas RLS (`\d+` nas tabelas relevantes, `SELECT` simulando tenants distintos).
- [ ] Testar `pgcrypto` com `docker compose exec backend python manage.py shell -c "..."` (criptografar/decriptar).
- [ ] Verificar obrigatoriedade do header `X-Tenant-Id` com requisições `curl` internas (via `docker compose exec backend curl`).

### 5. Qualidade Frontend Estática
- [ ] `pnpm lint` (inclui ESLint + regras FSD).
- [ ] `pnpm typecheck`.
- [ ] `pnpm format` (modo `--check`).
- [ ] Verificar ausência de avisos no console do Vite dev (`pnpm dev` breve smoke, usando tenant default).

### 6. Testes Frontend
- [ ] `pnpm test:coverage` garantindo cobertura ≥85% e revisar relatório `coverage/coverage-final.json`.
- [ ] `pnpm test:e2e` (Playwright em Chromium/Firefox/WebKit) registrando traces/videos se gerados.
- [ ] `pnpm storybook:build && pnpm storybook:test` assegurando stories sadios.
- [ ] Validar tags `@SC-00x` nos testes (grep em `frontend/tests`).

### 7. Fluxos CLI Fundamentais
- [ ] `pnpm foundation:scaffold feature <mock>` seguindo quickstart; validar geração de rotas, stores e métrica `sc_001_scaffolding_minutes`.
- [ ] `pnpm foundation:tokens pull --tenant tenant-alfa` seguido de `pnpm foundation:tokens build`; comparar diffs gerados com contratos.
- [ ] `pnpm foundation:otel verify --tenant tenant-alfa` conferindo spans, baggage `tenant_id` e mascaramento PII.
- [ ] Limpar artefatos temporários entre execuções (ex.: diretórios gerados, Storybook static).

### 8. Contratos e Pact
- [ ] `pnpm openapi:lint`.
- [ ] `pnpm openapi:diff` comparando `contracts/api.yaml` vs `api.previous.yaml`, validar saída sem breaking changes inesperadas.
- [ ] `pnpm openapi:generate` e confirmar ausência de diffs não comitados.
- [ ] `pnpm pact:verify` (Vitest) e revisar logs de cada interação.
- [ ] Validar `contracts/pacts/` e `frontend/tests/state/*.pact.ts` para estados/fixtures atualizados.

### 9. Performance e UX
- [ ] `pnpm perf:lighthouse` (playwright-lighthouse). Confirmar budgets (LCP ≤2.5s, TTI ≤3.0s, CLS ≤0.1). Exportar relatório HTML/JSON.
- [ ] `pnpm perf:smoke` (k6) armazenando `artifacts/.../k6-smoke.json`. Analisar thresholds e tempos p95/p99.
- [ ] Caso existam budgets definidos em `frontend/lighthouse.config.mjs`/`tests/performance/frontend-smoke.js`, garantir aderência sem warnings.

### 10. Segurança
- [ ] Executar testes específicos: `pnpm test --run tests/security` (ou filtro via Vitest) para CSP/Trusted Types.
- [ ] Revisar middleware CSP em tempo de execução (`curl` via docker, conferindo cabeçalhos `Content-Security-Policy`, `Report-To`).
- [ ] Validar Trusted Types no frontend em modo dev (`pnpm dev`, verificar console).
- [ ] Rodar `pnpm audit:frontend` (alta severidade fail-closed).

### 11. Observabilidade e Telemetria
- [ ] Confirmar export OTEL (`docker compose logs otel-collector` após `foundation:otel verify`).
- [ ] Verificar mascaramento de atributos (checar `frontend/tests/otel/masking.spec.ts` e logs).
- [ ] `pnpm finops:report` e garantir geração de `observabilidade/data/foundation-costs.json`.
- [ ] Validar dashboards `observabilidade/dashboards/frontend-foundation.json` (rodar `jq` para schema, conferir painéis SC-001..SC-005).
- [ ] Revisar runbook `docs/runbooks/frontend-foundation.md` e atualizar evidências se necessário.

### 12. Automação de CI/CD
- [ ] Rodar scripts `pnpm sbom:frontend`, `pnpm ci:outage` e conferir efeitos (labels simulados, evento OTEL).
- [ ] Validar workflow `.github/workflows/ci/frontend-foundation.yml` usando `act` ou checagens de lint YAML (`pnpm exec actionlint` se disponível ou `docker run rhysd/actionlint`).
- [ ] Garantir que job `contracts` executa Spectral, diff e Pact localmente (emular com `pnpm contracts:verify`).

### 13. Revisão de Documentação e Contratos
- [ ] Conferir `specs/002-f-10-fundacao/plan.md`, `research.md`, `data-model.md` para coerência com implementação.
- [ ] Validar ADRs (`docs/adr/adr-perf-front.md`) e LGPD (`docs/lgpd/rls-evidence.md`) quanto a alinhamento com evidências coletadas.
- [ ] Revisar harmonização `observabilidade/` vs `observability/` conforme T113 (busca com `rg "observability"`).

### 14. Evidências TDD & Histórico
- [ ] Consultar commits iniciais que deixaram testes em vermelho (git log/speckit) e garantir que os mesmos testes agora estão verdes.
- [ ] Registrar resumo das evidências em `artifacts/validacao-002-f-10/resumo.md` com listas de comandos, métricas e screenshots relevantes.

### 15. Checklist Final
- [ ] Todos os logs arquivados e verificados sem warnings.
- [ ] Nenhum diff sujo em git (`git status` limpo).
- [ ] Relatório final consolidado em `artifacts/validacao-002-f-10/relatorio-final.md` com conclusões, pendências e próximos passos (se houver).
- [ ] Atualizar runbook e painéis com aprendizados ou ajustes necessários pós-validação.

## Dependências e Riscos
- Segredos Vault podem não estar disponíveis em ambiente local; preparar variáveis mock e documentar diferenças.
- Comandos de performance (Lighthouse/k6) exigem recursos; mitigar rodando isoladamente e monitorando CPU/RAM.
 - Playwright pode requerer `pnpm exec playwright install chromium`; prever passo caso falte binário.
- Se `act` não estiver instalado, propor alternativa para validar workflow (ex.: `actionlint` remoto ou revisão manual).

## Estratégia de Comunicação
- Reportar qualquer bloqueio crítico imediatamente ao time via canal #foundation.
- Atualizar este plano com anotações (em pull request separado) se novos testes surgirem durante execução.
- Ao finalizar, preparar resumo executivo (máx. 1 página) para stakeholders com principais métricas e conclusões.
