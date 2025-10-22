# Tasks: F-10 Fundação Frontend FSD e UI Compartilhada

**Input**: Artefatos em `/home/pizzaplanet/meus_projetos/iabank/specs/002-f-10-fundacao/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)  
**Pré-requisitos**: `plan.md` aprovado; pendências do `/clarify` resolvidas/registradas; Node 20 + pnpm 9; Python 3.11; Docker local conforme `quickstart.md`

**Testes (Art. III)**: TDD é obrigatório nesta feature. Escreva testes primeiro e valide o estágio vermelho (falhando) antes da implementação. Registre o commit/execução que comprova o estado vermelho.

**Organização**: Tarefas agrupadas por user story (US1, US2, US3) para manter fatias verticais independentes. Itens marcados com [P] podem rodar em paralelo (arquivos domínios distintos).

## Fase 0: TDD & Contratos Obrigatórios (Art. III, Art. XI)

- [X] T001 [P] [FOUND] Preparar linters de contratos (Spectral) e script de diff OpenAPI (criar `contracts/.spectral.yaml`, `contracts/scripts/openapi-diff.sh` e `package.json` root com `scripts.openapi`)
- [X] T007 [P] [FOUND] Adicionar setup de performance: Lighthouse e k6 (arquivos: `frontend/lighthouse.config.mjs`, `tests/performance/frontend-smoke.js`) com budgets de UX; rodar e registrar falha inicial
- [X] T008 [FOUND] Adicionar job de CI “contracts” (arquivo: `.github/workflows/ci/frontend-foundation.yml`) que execute Spectral, OpenAPI-diff e Pact referenciando os testes por US (estado vermelho permitido até implementação)
- [X] T090 [P] [FOUND] Criar Pact inicial `frontend/tests/state/query-cache.pact.ts` cobrindo `GET /api/v1/tenants/{tenantId}/themes/current`, `POST /features/scaffold` e `GET /tenant-metrics` (estado vermelho controlado)
- [X] T091 [P] [FOUND] Adicionar teste RLS `backend/apps/tenancy/tests/test_rls_enforcement.py` validando políticas, pgcrypto e obrigatoriedade de `X-Tenant-Id` (estado vermelho controlado)

**Checkpoint**: Tarefas de TDD/contratos criadas e falhando (vermelho) – pronto para iniciar setup.

## Fase 1: Setup do Projeto (inicialização)

- [X] T009 [FOUND] Inicializar workspaces pnpm e Node (arquivos: `package.json` root com `workspaces`, `.nvmrc`, `.tool-versions`, `.npmrc` travando pnpm 9)
- [X] T010 [FOUND] Configurar formatação e lint base (arquivos: `.editorconfig`, `.prettierrc`, `.eslintignore`, `.gitignore`)
- [X] T011 [FOUND] Inicializar SPA React+TS+Vite em `frontend/` (arquivos: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/src/main.tsx`, `frontend/index.html`)
- [X] T012 [FOUND] Configurar Vitest + Testing Library (arquivos: `frontend/vitest.config.ts`, `frontend/setupTests.ts`, `frontend/src/tests/utils/test-utils.tsx`)
- [X] T013 [FOUND] Configurar Playwright básico para stories e smoke (arquivo: `frontend/playwright.config.ts`)
- [X] T014 [FOUND] Esqueleto CI “frontend-foundation” (arquivo: `.github/workflows/ci/frontend-foundation.yml`) com jobs vazios: `lint`, `test`, `contracts`, `visual-accessibility`, `performance`, `security`
- [X] T109 [FOUND] Popular job `lint` no CI com ESLint + `eslint-plugin-fsd-boundaries` (fail‑closed) e regras de boundaries + uso indevido de Zustand
- [X] T092 [P] [FOUND] Configurar Renovate (arquivo: `renovate.json`) e workflow `/.github/workflows/renovate-validation.yml` validando schema/assignees

**Checkpoint**: Projeto inicial executa `pnpm install`, `pnpm lint`, `pnpm test` básicos.

## Fase 2: Fundamentos Compartilhados (bloqueios globais)

### Base da plataforma

- [X] T015 [FOUND] Configurar TanStack Query com partição por tenant (arquivo: `frontend/src/shared/api/queryClient.ts` com chaves `['tenant', tenantId, ...]` e políticas via `meta.tags`; expor `resetOnTenantChange` para limpar `QueryClient` na troca de tenant)
- [X] T016 [FOUND] Configurar Zustand store para shell global (arquivo: `frontend/src/app/store/index.ts` com slices `tenant`, `theme`, `session`), com reset de estados sensíveis na troca de tenant
- [X] T017 [FOUND] Configurar client HTTP com `X-Tenant-Id` + Trace Context (arquivo: `frontend/src/shared/api/client.ts` com interceptors/fetch e headers `traceparent`/`tracestate`)
- [X] T018 [FOUND] Tipar variáveis de ambiente (arquivo: `frontend/src/shared/config/env.ts` + `frontend/.env.example` com `OTEL_*`, `TENANT_DEFAULT`)
- [X] T019 [FOUND] Ajustar managers de tenancy (arquivo: `backend/apps/tenancy/managers.py`) para injetar `tenant_id` automaticamente
- [X] T020 [FOUND] Habilitar `pgcrypto` e políticas RLS expandidas (arquivos: `backend/apps/tenancy/migrations/0025_enable_rls_frontend.py`, `backend/apps/tenancy/sql/rls_policies.sql`)
- [X] T021 [FOUND] Inicializar Observabilidade base (arquivo: `frontend/src/app/providers/telemetry.tsx` com stub de OTEL Web SDK)
- [X] T022 [FOUND] Criar runbook inicial (arquivo: `docs/runbooks/frontend-foundation.md` com procedimentos de flags, rollback e gates)
- [X] T023 [FOUND] Configurar geração de SBOM CycloneDX e auditorias (arquivo: `.github/workflows/ci/frontend-foundation.yml` – job `security`)
- [X] T024 [FOUND] Preparar base de contratos canônicos (arquivo: `contracts/api.yaml` seedado com `specs/002-f-10-fundacao/contracts/frontend-foundation.yaml` + script `pnpm openapi:generate`)

### Observabilidade e feature flags

- [ ] T093 [P] [FOUND] Integrar ConfigCat no frontend (`frontend/src/shared/config/flags.ts`, `frontend/src/app/providers/flags.tsx`) com fallback local e canário por tenant para `foundation.fsd` / `design-system.theming`
- [ ] T094 [P] [FOUND] Provisionar feature flags no backend (`backend/config/feature_flags.py`, `backend/apps/foundation/services/flag_gate.py`) aplicando rollout por tenant e fallback offline
- [ ] T095 [FOUND] Alinhar script de performance para `tests/performance/frontend-smoke.js` e atualizar `package.json`/job `performance` em `.github/workflows/ci/frontend-foundation.yml`

### Governança de contratos e secrets

- [ ] T064 [FOUND] OpenAPI TS client codegen e wiring (`frontend/src/shared/api/generated`, script `pnpm openapi:generate` e uso nos serviços)
- [ ] T065 [FOUND] Variáveis de ambiente frontend: adicionar `FOUNDATION_CSP_NONCE`, `FOUNDATION_TRUSTED_TYPES_POLICY`, `FOUNDATION_PGCRYPTO_KEY` em `frontend/src/shared/config/env.ts` e `frontend/.env.example`
- [ ] T066 [FOUND] Fallback de Vault em dev: documentar e implementar fallback seguro em `docs/runbooks/frontend-foundation.md`
- [ ] T067 [FOUND] Estender `ApiContractArtifact` (campos `breaking_change`, `released_at`) em `backend/apps/contracts/models.py` + migração
- [ ] T068 [FOUND] Criar `ContractDiffReport` em `backend/apps/contracts/models.py` + migração e admin
- [ ] T069 [FOUND] Sinais em `backend/apps/contracts/signals.py` para persistir resultados de Spectral/OpenAPI-diff (job `contracts`)

**Checkpoint**: Fundamentos prontos. US1/US2/US3 podem iniciar em paralelo.

## Fase 3: User Story 1 — Scaffolding FSD Convergente (Prioridade P1)

### Testes (executar antes da implementação)
- [ ] T025 [P] [US1] Pact consumer de scaffolding (arquivo: `contracts/pacts/frontend-consumer/register_feature_scaffold.pact.ts`)
- [ ] T026 [P] [US1] Teste de CLI de scaffolding (arquivo: `frontend/tests/scaffolding/scaffolding.spec.ts`)
- [ ] T027 [P] [US1] Teste DRF para `POST /api/v1/tenants/{tenantId}/features/scaffold` (arquivo: `backend/apps/foundation/tests/test_register_feature_scaffold.py`)
- [ ] T097 [P] [US1] Teste Playwright e2e (`frontend/tests/e2e/foundation.scaffold.spec.ts`) validando roteamento multi-tenant, tempo <5min e ausência de PII em URLs

### Implementação
- [ ] T028 [US1] Modelo `FeatureTemplateRegistration` (arquivo: `backend/apps/foundation/models/feature_template_registration.py`)
- [ ] T029 [US1] Serializer `FeatureTemplateRegistrationSerializer` (arquivo: `backend/apps/foundation/serializers/feature_template.py`)
- [ ] T030 [US1] View/URL DRF `registerFeatureScaffold` (arquivo: `backend/apps/foundation/api/views.py`, `backend/apps/foundation/api/urls.py`)
- [ ] T031 [US1] Serviço `ScaffoldRegistrar` (arquivo: `backend/apps/foundation/services/scaffold_registrar.py`)
- [ ] T032 [US1] Migração `0002_frontend_foundation_backfill.py` (arquivo: `backend/apps/foundation/migrations/0002_frontend_foundation_backfill.py`)
- [ ] T033 [P] [US1] CLI `foundation:scaffold` (arquivo: `frontend/scripts/scaffolding/index.ts` + script em `frontend/package.json`)
- [ ] T034 [P] [US1] Registrar no roteador multi-tenant (arquivo: `frontend/src/app/providers/router.tsx` + atualização `frontend/src/app/index.tsx`)
- [ ] T035 [US1] Lint FSD e governança de imports + regra de uso de Zustand (banir estado local/efêmero em store) (arquivos: `frontend/.eslintrc.cjs`, `frontend/scripts/eslint-plugin-fsd-boundaries/`)
- [ ] T036 [US1] Atualizar `quickstart.md` com fluxo final (arquivo: `specs/002-f-10-fundacao/quickstart.md`)
- [ ] T037 [US1] Instrumentar tempo de scaffolding (SC-001) (arquivo: `backend/apps/foundation/services/scaffold_registrar.py` + métrica em `observabilidade/dashboards/frontend-foundation.json`, alimentando painel DORA: lead time p95 < 30h úteis)

### Resiliência e controles adicionais

- [ ] T070 [US1] Enforçar `Idempotency-Key` (unicidade por tenantId+featureSlug; TTL 86400; ecoar cabeçalho na resposta 201)
- [ ] T071 [US1] Gerar e validar `ETag` nas respostas de scaffolding (If-None-Match)
- [ ] T072 [US1] Rate limiting 30/min para `POST /features/scaffold` com `django-ratelimit` e cabeçalho `Retry-After`

**Checkpoint**: US1 completa; CLI gera FSD, backend registra scaffolding e gates verdes.

## Fase 4: User Story 2 — Design System Multi-tenant Observável (Prioridade P2)

### Testes (executar antes da implementação)
- [ ] T038 [P] [US2] Pact consumer para `GET /api/v1/tenants/{tenantId}/themes/current` (arquivo: `contracts/pacts/frontend-consumer/get_tenant_theme.pact.ts`)
- [ ] T039 [P] [US2] Test runner de acessibilidade para Storybook (arquivo: `frontend/.storybook/test-runner.ts` com axe-core) — falhar se houver violações WCAG 2.2 AA
- [ ] T040 [P] [US2] Stories de componente `Button` com variações por tenant + asserções de tema (arquivo: `frontend/src/shared/ui/button/Button.stories.tsx`)

### Implementação
- [ ] T041 [US2] Modelo `TenantThemeToken` (arquivo: `backend/apps/tenancy/models/tenant_theme_token.py`)
- [ ] T042 [US2] Serializer de tema (arquivo: `backend/apps/foundation/serializers/theme.py`)
- [ ] T043 [US2] View DRF `getTenantTheme` (arquivo: `backend/apps/foundation/api/views.py` + rota)
- [ ] T044 [US2] Script `foundation:tokens` (pull/build) (arquivos: `frontend/scripts/tokens/index.ts`, `frontend/package.json` scripts)
- [ ] T045 [P] [US2] Tailwind config com tokens e CSS vars (arquivo: `frontend/tailwind.config.ts`)
- [ ] T046 [US2] Configuração de tenants (arquivo: `frontend/src/shared/config/theme/tenants.ts`)
- [ ] T047 [US2] CSS de tokens (arquivo: `frontend/src/shared/ui/tokens.css`)
- [ ] T048 [P] [US2] Storybook multi-tenant (arquivos: `frontend/.storybook/main.ts`, `frontend/.storybook/preview.ts` com `html[data-tenant]`)
- [ ] T049 [P] [US2] Componente `Button` + API pública (arquivos: `frontend/src/shared/ui/button/index.ts`, `frontend/src/shared/ui/button/Button.tsx`)
- [ ] T052 [P] [US2] Componentes base de estado de dados (Skeleton, Empty, Error) em `frontend/src/shared/ui/` + stories e testes alinhados a FR-005c
- [ ] T050 [US2] Job Chromatic no CI (arquivo: `.github/workflows/ci/frontend-foundation.yml` – job `visual-accessibility` com cobertura >=95% — releases fail-closed; non-release fail-open)
- [ ] T098 [US2] Criar `frontend/scripts/chromatic/check-coverage.ts` e integrar no job `visual-accessibility` para validar cobertura >=95% por tenant
- [ ] T110 [FOUND] Popular job `visual-accessibility` no CI integrando Chromatic + axe (Storybook) com gates: cobertura >=95% por tenant e WCAG 2.2 AA (fail‑closed em release)

### Observabilidade e governança adicionais

- [ ] T073 [P] [US2] Validar tema com Zod `TokenSchema` (backend serializer + compile step frontend)
- [ ] T074 [P] [US2] Ingerir auditoria WCAG em `TenantThemeToken.wcag_report` e gate antes de `is_default=true`
- [ ] T075 [US2] Modelo `DesignSystemStory` + migração (`backend/apps/foundation/models/design_system_story.py`)
- [ ] T076 [P] [US2] Serializer/mapeamento de metadados (Chromatic/axe → campos do modelo)
- [ ] T077 [US2] `DesignSystemStoryViewSet.list` com paginação e filtros (`componentId`, `tag`) + rotas DRF
- [ ] T078 [P] [US2] Teste API/Pact consumer para `GET /api/v1/design-system/stories`

**Checkpoint**: US2 completa; tokens por tenant aplicados, stories cobrem >=95% e a11y OK.

## Fase 5: User Story 3 — Telemetria, Pactos e Controles de Privacidade (Prioridade P3)

### Testes (executar antes da implementação)
- [ ] T051 [P] [US3] Verificação de OTEL no cliente (arquivo: `frontend/tests/otel/propagation.spec.ts` com spans e baggage `tenant_id`) e medição de cobertura de spans >90% das interações críticas (NFR-003)
- [ ] T052 [P] [US3] Teste de mascaramento de PII (arquivo: `frontend/tests/otel/masking.spec.ts` cobrindo regex de CPF/email/telefone)
- [ ] T053 [P] [US3] Scanner CSP/Trusted Types (arquivo: `frontend/tests/security/csp_trusted_types.spec.ts` validando report-only → enforce)
- [ ] T054 [P] [US3] Pact consumer para `GET /api/v1/tenant-metrics/{tenantId}/sc` (arquivo: `contracts/pacts/frontend-consumer/list_sc_metrics.pact.ts`)

### Implementação
- [ ] T055 [US3] Provedor OTEL Web (arquivo: `frontend/src/app/providers/telemetry.tsx` com `@opentelemetry/sdk-trace-web` e `BaggagePropagator`)
- [ ] T056 [US3] Provedor de segurança (arquivo: `frontend/src/app/providers/security.tsx` com Trusted Types policy `foundation-ui`)
- [ ] T057 [US3] Middleware Vite dev para CSP nonce (arquivo: `frontend/vite.csp.middleware.ts` injetando `nonce` em `index.html`)
- [ ] T058 [US3] Middleware/Settings Django para CSP (arquivos: `backend/apps/foundation/middleware/security.py`, `backend/settings.py` atualizando cabeçalhos)
- [ ] T059 [US3] Endpoint `listTenantSuccessMetrics` (arquivo: `backend/apps/foundation/api/views.py` + paginação e headers de RateLimit)
- [ ] T060 [US3] Utilitário `sanitizeTelemetryAttributes` (arquivo: `frontend/src/shared/lib/telemetry/masking.ts`)
- [ ] T099 [US3] Implementar CLI `pnpm foundation:otel verify` (`frontend/scripts/otel/verify.ts`) disparando traces com baggage e validando mascaramento

### Pós-ativação

- [ ] T079 [US3] Tornar CSP enforce após janela de report-only (30 dias) + testes de TTL de exceções

**Checkpoint**: US3 completa; telemetria correlaciona com backend, CSP/Trusted Types ok e políticas de PII ativas.

## Fase Final: Observabilidade, Segurança e Cross-Cutting

### Runbooks e operações

- [ ] T061 [FOUND] Dashboard SC-001..SC-005 (arquivo: `observabilidade/dashboards/frontend-foundation.json`), incluindo painel de Error Budget (5% mensal; alerta/pausa ao atingir 80%)
- [ ] T062 [FOUND] Atualizar runbook com evidências de rollout/gates (arquivo: `docs/runbooks/frontend-foundation.md`)
- [ ] T113 [FOUND] Harmonizar referências “observability/” vs “observabilidade/” em documentos legados (ex.: `docs/adr/adr-perf-front.md:16`, instruções que citam `scripts/observability/check_structlog.py`) sem renomear diretórios/arquivos existentes
- [ ] T063 [FOUND] Garantir tags `@SC-00x` em testes e PRs (arquivos: `frontend/tests/**/*`, `.github/workflows/ci/frontend-foundation.yml`)
- [ ] T100 [FOUND] Criar `scripts/finops/foundation-costs.ts` coletando uso Chromatic/Lighthouse/pipelines e integrando com `observabilidade/dashboards/frontend-foundation.json` + runbook
- [ ] T101 [FOUND] Implementar `scripts/ci/handle-outage.ts` e integrar job `ci-outage-guard` para aplicar label `ci-outage`, registrar justificativa e emitir evento OTEL
- [ ] T105 [P] [FOUND] Registrar ADR `docs/adr/adr-perf-front.md` formalizando uso conjunto de Lighthouse+k6
- [ ] T106 [P] [FOUND] Criar `docs/lgpd/rls-evidence.md` com scripts/checklists de verificação RLS e PII

### Segurança e conformidade

- [ ] T080 [P] [FOUND] Configurar Sentry no backend (DSN, sampling, PII scrubbing)
- [ ] T081 [P] [FOUND] Configurar Sentry no frontend (SDK init em `app/providers/telemetry.tsx`)
- [ ] T082 [P] [FOUND] Habilitar `django-prometheus` (middleware, endpoint `/metrics`, scrape notes)
- [ ] T083 [P] [FOUND] Configurar `structlog` JSON com redatores de PII
- [ ] T084 [P] [FOUND] Gate de cobertura: Vitest + Python coverage ≥ 85% (releases fail-closed)
- [ ] T085 [P] [FOUND] Gate de complexidade: ESLint `complexity <= 10` + `radon cc <= 10`
- [ ] T086 [P] [FOUND] SAST (Semgrep) com política de severidade (releases fail-closed)
- [ ] T087 [P] [FOUND] DAST (OWASP ZAP baseline) contra stack local (releases fail-closed)
- [ ] T088 [P] [FOUND] SCA: pnpm audit + Poetry safety/pip-audit + SBOM validate (fail para High/Critical)
- [ ] T112 [FOUND] Popular job `security` no CI agregando SAST (Semgrep), DAST (ZAP), SCA (pnpm audit + safety/pip-audit) e SBOM CycloneDX (fail‑closed em release)
- [ ] T102 [P] [FOUND] Adicionar `docs/security/threat-model-template.md` com estrutura STRIDE/LINDDUN oficial
- [ ] T103 [FOUND] Versionar primeiro artefato `docs/security/threat-models/frontend-foundation/v1.0.md` preenchendo sessão inicial
- [ ] T104 [FOUND] Incluir job `ci/threat-model-lint` em `.github/workflows/ci/frontend-foundation.yml` validando presença/atualização do threat model

### Observabilidade e métricas avançadas

- [ ] T089 [P] [FOUND] Playwright-Lighthouse com budgets (LCP ≤ 2.5s, TTI ≤ 3.0s) e gates no CI
- [ ] T111 [FOUND] Popular job `performance` no CI integrando Playwright-Lighthouse com budgets (LCP ≤ 2.5s, TTI ≤ 3.0s) e publicar evidências no dashboard
- [ ] T107 [FOUND] Instrumentar métricas `foundation_frontend_cpu_percent`/`foundation_frontend_memory_percent` via sidecar Prometheus (`infra/argocd/frontend-foundation/`) e alerts HPA
- [ ] T108 [FOUND] Publicar métrica `foundation_api_throughput` (k6 → OTEL) e automatizar alerta/ticket `@SC-001` (`tests/performance/frontend-smoke.js`, `scripts/observabilidade/alert-handler.ts`, dashboards)

---

## Dependências

- Ordem de fases: TDD & Contratos (Fase 0) → Setup (Fase 1) → Fundamentos (Fase 2) → US1/US2 em paralelo (Fases 3 e 4) → US3 (Fase 5).  
- Dependências por história:
  - US1 depende de: Fundamentos (T015–T024). Independente de US2/US3.
  - US2 depende de: Fundamentos (T015–T024). Independente de US1/US3.
  - US3 depende de: Fundamentos (T015–T024). Integra com métricas de US1/US2 quando disponíveis, mas pode iniciar em paralelo.

## Exemplos de Paralelização

- US1: T033 (CLI) [P] em paralelo com T028–T032 (backend) e T034 (rotas) [P].
- US2: T045 (Tailwind) [P], T048 (Storybook) [P] e T049 (Button) [P] em paralelo após T041–T043 iniciarem, ou usando tokens mock gerados por T044 em dev/local.
- US3: T055 (OTEL) [P], T056 (Security) [P] e T058 (CSP backend) [P] podem evoluir em paralelo.

## Critérios de Teste Independente por História

- US1: CLI `foundation:scaffold` gera FSD completa, passa lint FSD, backend persiste `FeatureTemplateRegistration` e tempo alimenta SC-001; Pact e DRF tests verdes.
- US2: `GET /tenants/{tenantId}/themes/current` retorna tokens válidos; Storybook/Chromatic >=95% de cobertura e `axe` sem violações; componente `Button` alterna estilos por tenant.
- US3: Traços do frontend incluem `tenant_id` no baggage e correlacionam com backend; scanner não encontra PII em URLs/telemetria; CSP report-only sem violações e enforce sem regressões; endpoint de métricas pagina resultados.

## Estratégia de Implementação (MVP → incremental)

- MVP: Concluir US1 (scaffolding FSD + registro backend) com Fundamentos e Setup mínimos para destravar squads (atinge SC-001, SC-003 parcialmente).
- Iteração 2: US2 (design system multi-tenant com Chromatic/a11y) para consolidar SC-002/SC-004.
- Iteração 3: US3 (OTEL + CSP/Trusted Types + métricas) para fechar SC-005 e observabilidade.

## Contagem de Tarefas

 - Total: 108
 - Por história: US1 = 17, US2 = 21, US3 = 12
- TDD & Contratos = 5, Setup = 7, Fundamentos = 19, Final = 22
 - Oportunidades de paralelização: 41 tarefas marcadas [P]
