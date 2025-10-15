# Implementation Plan: F-10 Fundação Frontend FSD e UI Compartilhada

**Branch**: `002-f-10-fundacao` | **Date**: 2025-10-14 | **Spec**: /home/pizzaplanet/meus_projetos/iabank/specs/002-f-10-fundacao/spec.md  
**Input**: Feature specification from `/home/pizzaplanet/meus_projetos/iabank/specs/002-f-10-fundacao/spec.md`

**Note**: Este template é preenchido pelo comando `/speckit.plan`. Consulte `documentacao_oficial_spec-kit/templates/commands/plan.md` para o fluxo completo sobre o que informar nessa fase.

## Summary

Estabelecer a fundação frontend descrita em `/home/pizzaplanet/meus_projetos/iabank/specs/002-f-10-fundacao/spec.md`, convergindo o scaffolding FSD, Storybook/Chromatic e o design system Tailwind multi-tenant alinhado a `BLUEPRINT_ARQUITETURAL.md §4` e `adicoes_blueprint.md` itens 1, 2 e 13. O plano reforça governança de contratos OpenAPI/Pact, propagação de OpenTelemetry/Trace Context e controles de segurança (CSP rígida, Trusted Types, PII masking) requeridos pela Constituição v5.2.0 (Art. I, III, VII, VIII, XI, XIII, XVIII). Hipóteses e limites de CI (gates de perf, SAST/SCA/SBOM, tags `@SC-xxx`) permanecem vigentes e sem pendências conforme clarificações registradas na especificação.

## Technical Context

**Backend**: Django 4.2 LTS + DRF 3.15 em `/home/pizzaplanet/meus_projetos/iabank/backend`, mantendo monolito modular com apps `tenancy`, `contracts` e `audit` para RLS, OpenAPI 3.1 e mascaramento de PII (Art. I, XI, XIII; ADR-010, ADR-011). Schema versionado em `contracts/api.yaml` com codegen determinístico.  
**Frontend**: SPA React 18 + TypeScript 5.6 + Vite 5 em `/home/pizzaplanet/meus_projetos/iabank/frontend`, estrutura FSD (`app/pages/features/entities/shared`) conforme Blueprint §4; TanStack Query 5 para dados particionados por tenant, Zustand 4 para estado global, Hooks nativos para local (Art. I; adicoes_blueprint.md §13).  
**Async/Infra**: Celery 5.3 + Redis 7 para fila de tarefas pact/Chromatic/lighthouse no CI e jobs de sincronização de tokens; provisionamento descrito em Terraform + Argo CD manifests (`infra/terraform`, `infra/argocd`) alinhados ao Art. I e XIV.  
**Persistencia/Dados**: PostgreSQL 15 com pgcrypto habilitado para campos PII (CPF, email) e políticas RLS por tenant aplicadas nas views expostas ao frontend; managers garantem `tenant_id` automático (Art. I, X, XIII; adicoes_blueprint.md §4).  
**Testing**: TDD obrigatório com Vitest + Testing Library para UI, Playwright para scaffolding end-to-end e Jest Pact para consumidores; Spectral/OpenAPI-diff, k6 e Lighthouse gates integrados ao pipeline (Art. III, IX; ADR-011, clarificação Perf-Front).  
**Observabilidade**: OpenTelemetry JS SDK com W3C Trace Context e baggage de `tenant_id` propagada; integração com collector padronizado e Sentry para front/back; mascaramento de PII via allowlist/blocklist (Art. VII; ADR-012).  
**Seguranca/Compliance**: CSP nonce com `script-src 'strict-dynamic' 'nonce-{...}'` e política de Trusted Types (30 dias em Report‑Only → enforce), sanitização de sinks, política de PII em URLs/telemetria, Vault para segredos front/back (Art. XII, XIII, XVI; adicoes_blueprint.md §13).  
**Project Type**: Monorepo com `backend/`, `frontend/`, `infra/`, `contracts/` e `docs/`, obedecendo o fluxo `constitution → specify → clarify → plan → tasks` e guard rails do Blueprint (Art. I, II, XVIII).  
**Performance Targets**: SLO UX (LCP ≤ 2.5s p95, TTI ≤ 3.5s) monitorados por Lighthouse budgets; DORA lead time < 1 dia e erro < 15%; TanStack Query caches por criticidade (`meta.tags`) sustentam SC-001/SC-002 (Art. VI, VIII, IX).  
**Restricoes**: TDD pré-implementação, expand/contract para mudanças de schema, RLS obrigatório, Trusted Types enforcement, tags `@SC-xxx`, fail-closed para contratos/Chromatic/Lighthouse em release; sem pendências de clarificação (Art. III, IX, XI, XIII, XVIII).  
**Escopo/Impacto**: Afeta `frontend/` (scaffolding FSD, Storybook, Tailwind tokens), `backend/apps/tenancy` (managers RLS), `contracts/api.yaml`, `contracts/pacts/frontend-consumer/`, CI pipelines (GitHub Actions), `docs/design-system/`, `infra/terraform` e `infra/argocd` para GitOps rollouts multi-tenant.

## Constitution Check

*GATE: Validar antes da Fase 0 e reconfirmar após o desenho de Fase 1.*

- [ ] **Art. III - TDD**: Tests iniciarão com `frontend/tests/scaffolding/scaffolding.spec.ts`, `frontend/tests/state/query-cache.pact.ts` e `backend/apps/tenancy/tests/test_rls_enforcement.py`, assegurando falha controlada antes da implementação.  
- [ ] **Art. VIII - Lançamento Seguro**: Feature flags `foundation.fsd` e `design-system.theming` gerenciadas via ConfigCat (fallback local) com canary por tenant e orçamento de erro vinculado aos SLOs SC-001/SC-002; rollback documentado em `docs/runbooks/frontend-foundation.md`. Diretrizes operacionais de CSP/Trusted Types detalhadas em "Observability & Security Implementation".  
- [ ] **Art. IX - Pipeline CI**: Pipeline `ci/frontend-foundation.yml` executará Vitest (≥85% cobertura), ESLint FSD, Spectral, OpenAPI-diff, Pact, Chromatic (cobertura visual ≥95% por tenant com gate), Lighthouse (orçamentos), k6 smoke e geração/validação de SBOM CycloneDX; complexidade monitorada via Sonar/ESLint rules.  
- [ ] **Art. XI - Governança de API**: OpenAPI 3.1 (`contracts/api.yaml`) atualizado contrato-primeiro, diffs validados antes de merge, codegen `frontend/scripts/gen-api-types.ts`, Pact consumer `frontend/contracts/pact/frontend-backend.json` com versionamento SemVer.  
- [ ] **Art. XIII - Multi-tenant & LGPD**: Políticas RLS em `backend/apps/tenancy/migrations/` com testes de isolamento, managers enforce `tenant_id`, TanStack Query keys `['tenant', tenantId, ...]`, PII criptografada via pgcrypto; auditoria em `docs/lgpd/rls-evidence.md`.  
- [ ] **Art. XVIII - Fluxo Spec-Driven**: `spec.md` e futura `tasks.md` manterão links cruzados; nenhuma pendência em `/clarify`; este plano atualiza `plan.md` e seguirá com geração de `research.md`, `data-model.md`, `quickstart.md` conforme fluxo oficial.

## Project Structure

### Documentação (esta feature)

```
/home/pizzaplanet/meus_projetos/iabank/specs/002-f-10-fundacao/
|-- plan.md            # plano alinhado ao Art. XVIII
|-- research.md        # decisões Phase 0 (resolução de NEEDS CLARIFICATION)
|-- data-model.md      # entidades compartilhadas frontend/backend
|-- quickstart.md      # instruções de bootstrap para squads
|-- contracts/         # OpenAPI/Pact específicos da fundação
|   `-- frontend-foundation.yaml
`-- tasks.md           # desdobramento para implementação (Phase 2 em diante)
```

### Código-Fonte (repositório)

```
/home/pizzaplanet/meus_projetos/iabank/frontend/
|-- package.json
|-- vite.config.ts
|-- tailwind.config.cjs
|-- src/
    |-- app/
    |-- pages/
    |-- features/
    |-- entities/
    `-- shared/
/home/pizzaplanet/meus_projetos/iabank/backend/
|-- apps/
|   |-- tenancy/
|   |-- contracts/
|   `-- audit/
|-- config/settings/
/home/pizzaplanet/meus_projetos/iabank/contracts/
|-- api.yaml
|-- api.previous.yaml
`-- pacts/frontend-consumer/
/home/pizzaplanet/meus_projetos/iabank/docs/
|-- design-system/
|-- runbooks/
/home/pizzaplanet/meus_projetos/iabank/.github/workflows/
`-- ci/frontend-foundation.yml
```

**Structure Decision**: Adoção de `/frontend` com camadas FSD (`app → pages → features → entities → shared`) garante alta coesão e alinhamento ao Art. I/II e Blueprint §4, enquanto `/backend/apps` mantém domínio segregado por app conforme Art. II. A criação de `contracts/pacts/frontend-consumer` e atualização de `api.yaml` reforçam o contrato-primeiro do Art. XI. Diretórios adicionais (`docs/runbooks`, `.github/workflows/ci/frontend-foundation.yml`) são necessários para operacionalizar os gates constitucionais sem introduzir acoplamento desnecessário.

## Testing & Quality Scope

- **Vitest (frontend/tests/scaffolding/scaffolding.spec.ts)**: Deve cobrir geração de estrutura (`app/pages/features/entities/shared`), criação de arquivos `index.ts`, registro no roteador multi-tenant, injeção TanStack Query/Zustand e validação dos `@SC-001/@SC-003` no manifesto. Casos esperados: sucesso tenant Alfa, sucesso tenant Beta, falha por lint (mock de CLI retornando erros), falha por idempotency-key repetida.
- **Playwright (frontend/tests/e2e/foundation.scaffold.spec.ts)**: Simular comando CLI via UI devtools, confirmar roteamento por subdomínio, verificar placeholders de loading/erro definidos na clarificação (skeleton/spinner/toast) e garantir ausência de PII em URL. Cenários: scaffolding completo <5min (timer medido), login multi-tenant, fallback de path em dev.
- **Pact (frontend/tests/state/query-cache.pact.ts)**: Contratos para `GET /api/v1/tenants/{tenantId}/themes/current`, `POST /features/scaffold`, `GET /tenant-metrics`. Cobrir status 200/201/202, 409, 422 e `application/problem+json` com RFC 9457. Anexar tags `@SC-003`.
- **Django Tests (backend/apps/tenancy/tests/test_rls_enforcement.py)**: Validar políticas RLS e managers (`TenantThemeTokenManager`, `FeatureTemplateRegistrationManager`) impedindo cross-tenant. Incluir testes para pgcrypto (`tenant_theme_token.json_payload` encriptado), ETag/idempotência (`POST scaffold` repetido), `X-Tenant-Id` obrigatório.
- **Lighthouse Budgets**: Configurar `frontend/lighthouse.config.mjs` com metas LCP ≤ 2.5s, TTI ≤ 3.5s, CLS ≤ 0.1. Executar via `pnpm lighthouse --config ...` e falhar PR se budgets estourarem (Art. IX).
- **k6 Smoke**: Script `tests/performance/frontend-smoke.js` exercendo endpoints de scaffolding (p95 < 500ms), tokens e métricas com cabeçalhos `X-Tenant-Id`, `traceparent`. Exportar resultados para dashboards SLO (`SC-001`, `SC-002`).
- **Chromatic + axe-core**: Stories críticos (Button, Card, LayoutShell, TenantSwitcher) devem ter variações Alfa/Beta/default com cobertura ≥95% e zero violações `axe`. Falhas bloqueiam merge (fail-closed). O job de CI deve validar a cobertura via script (`frontend/scripts/chromatic/check-coverage.ts`) e falhar abaixo do threshold.

## Backend Integration Notes

- **Apps e Localização**: 
  - `backend/apps/tenancy/` receberá modelos `TenantThemeToken`, managers (`TenantThemeTokenManager`, `TenantScopedQuerySet`), migrações de RLS (`0025_enable_rls_frontend.sql`) e serviços de sincronização.
  - `backend/apps/foundation/` (novo app) encapsulará views DRF (`ThemeViewSet`, `FeatureScaffoldView`, `TenantMetricViewSet`), serializers e validações específicas da fundação.
  - `backend/apps/contracts/` armazenará `ApiContractArtifact` e `ContractDiffReport` com sinais para lint/diff.
- **Migração Expand/Contract** (nomenclatura padronizada):
  1. Expand: criar tabelas e políticas RLS (migração `0001_frontend_foundation_expand.py`) com permissões `tenant_id = current_setting('app.tenant_id')`.
  2. Backfill: script Celery (`foundation/tasks/backfill_tokens.py`) para migrar tokens existentes do design system.
  3. Contract: remover campos legados após verificação (migração `0003_frontend_foundation_contract.py`).
  - Observação: migrações do app `tenancy` manterão sequência própria; habilitação adicional de RLS relacionada à fundação deve seguir nomenclatura do app `foundation` quando aplicável, evitando duplicidade de números (ex.: `backend/apps/foundation/migrations/0001_*`).
- **pgcrypto & Vault**: Configurar extensão `pgcrypto` na migração expand; chaves de criptografia referenciadas via Vault (`VAULT_TRANSIT_KEY_FOUNDATION`), com testes garantindo decriptação apenas via funções autorizadas.
- **Managers**: `TenantScopedManager` injeta `tenant_id` automático em `FeatureTemplateRegistration`. Tests devem cobrir tentativas sem tenant.

## API Implementation Mapping

- **Views/Serializers**:
  - `ThemeViewSet.retrieve_current` para `/themes/current`: utiliza serializer `TenantThemeSerializer` (fields: `tenantId`, `version`, `categories`, `wcagReport`) e adiciona cabeçalhos `ETag`, `RateLimit-*`.
  - `FeatureScaffoldView` (APIView) trata `POST /features/scaffold`: valida `Idempotency-Key`, chama serviço `ScaffoldRegistrar` (idempotent storing, queue Celery job para lint/test).
  - `TenantMetricViewSet.list` agrega métricas SC via `FeatureTemplateMetric` + caches Redis.
  - `DesignSystemStoryViewSet.list` fornece stories paginadas com `componentId`/`tag` filters, convertendo acessibilidade do Chromatic/axe.
- **Rate Limiting & Concurrency**: usar `django-ratelimit` com limites por tenant e burst/backoff:
  - `POST /features/scaffold`: 30/min (chave `foundation_scaffold:{tenant}`), burst 2×, com `Retry-After`.
  - `GET /tenants/{id}/themes/current`: 120/min, com ETag forte (W/"…") e cache client-side controlado.
  - `GET /tenant-metrics`: 60/min, com paginação obrigatória.
  - `GET /design-system/stories`: 120/min.
  - ETag via `hashlib.sha256` do payload serializado.
- **Integration with TanStack Query**: Documentar chaves de cache por endpoint:
  - `getTenantTheme`: `['tenant', tenantId, 'theme']`
  - `registerFeatureScaffold`: `['tenant', tenantId, 'scaffold', featureSlug]`
  - `listTenantMetrics`: `['tenant', tenantId, 'metrics', page, filters]`
- **Error Handling**: Implementar `ProblemDetailsExceptionHandler` reutilizando RFC 9457; mapear 409 (ETag mismatch), 422 (lint/test failure).

## Tooling & Automation Deliverables

- **CLI Scaffolding**: Criar pacote `frontend/scripts/foundation-cli` com comando `pnpm foundation:scaffold`. Estrutura:
  - `src/index.ts`: entrypoint CLI (Commander).
  - `src/generators/*`: templates FSD (TanStack, Zustand, story skeletons).
  - `src/services/metrics.ts`: coleta duração, envia para endpoint metrics.
  - Testes no Vitest (`__tests__/scaffold.cli.spec.ts`) cobrindo sucesso/falhas.
- **Tokens Pipeline**: Scripts `pnpm foundation:tokens pull/build` residem em `frontend/scripts/tokens/`. Utilizar `node-fetch` para baixar JSON do backend, `fs` para atualizar `shared/config/theme/tenants.ts` e `tokens.css`. Tests `tokens.spec.ts` garantem sincronismo com `docs/design-system/tokens.md`.
- **Observabilidade CLI**: `pnpm foundation:otel verify` em `frontend/scripts/otel/verify.ts` gera trace `FOUNDATION-TENANT-BOOTSTRAP`, injeta baggage `tenant_id`, `feature_name`, valida mascaramento (checa se PII é omitido) e grava relatório.
- **CI Workflow**: `/.github/workflows/ci/frontend-foundation.yml` com jobs:
  1. `lint` (ESLint + lint-fsd rules).
  2. `test` (Vitest, Playwright, Pact, coverage ≥ 85%).
  3. `contracts` (Spectral, OpenAPI-diff, Pact publish).
  4. `visual-accessibility` (Chromatic + axe) com gate de cobertura ≥95% por tenant.
  5. `performance` (Lighthouse budgets + k6).
  6. `security` (npm audit, dependabot check, Snyk optional, SBOM CycloneDX geração/validação com gate por severidade alta).
- **Linter Rules**: Custom ESLint plugin `eslint-plugin-fsd-boundaries` configurado em `frontend/.eslintrc.cjs`, com testes e regras import path.

## Observability & Security Implementation

- **OTEL**: Inicializar `@opentelemetry/sdk-trace-web` em `frontend/src/app/providers/telemetry.tsx` com exporters para OTLP e Sentry, habilitar `BaggagePropagator` com `tenant_id`, `feature_slug`. Backend usa `django-opentelemetry` integrando com as mesmas chaves. Variáveis mínimas: `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, `OTEL_RESOURCE_ATTRIBUTES`.
- **Masking**: Implementar `sanitizeTelemetryAttributes(attributes)` reutilizado em front/back para aplicar allowlist (tenantId, featureSlug, metricCode) e redaction (`[PII]`) em campos livres. Tests unitários asseguram redaction.
  - Baseline PII (não permitido em URLs/telemetria): CPF, CNPJ, email, telefone, endereço, nome completo, data de nascimento, documento (RG/Passaporte), geolocalização precisa, qualquer identificador de cliente.
  - Heurísticas mínimas: regex de CPF (`\b\d{3}\.\d{3}\.\d{3}-\d{2}\b`), email (`[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}` case-insensitive), telefone internacional, e chaves (`cpf|email|phone|document|address|name`).
- **CSP**: Aplicar cabeçalhos no gateway/CDN (prod) e middleware de dev (local). Report‑Only por 30 dias, depois enforcement.
  - Report‑Only exemplo: `Content-Security-Policy-Report-Only: default-src 'none'; base-uri 'self'; connect-src 'self' https://api.iabank.com https://staging-api.iabank.com; font-src 'self'; img-src 'self' data:; script-src 'self' 'strict-dynamic' 'nonce-{RANDOM}'; style-src 'self'; object-src 'none'; frame-ancestors 'none'; report-uri https://csp-report.iabank.com`.
  - Enforce exemplo: `Content-Security-Policy: default-src 'none'; base-uri 'self'; connect-src 'self' https://api.iabank.com https://staging-api.iabank.com; font-src 'self'; img-src 'self' data:; script-src 'self' 'strict-dynamic' 'nonce-{RANDOM}'; style-src 'self'; object-src 'none'; frame-ancestors 'none'`.
  - Injeção de `nonce`: gateway (NJS/Nginx) insere atributo `nonce` em todas as tags `<script>` do `index.html` no edge; em dev, plugin Vite middleware injeta `nonce` nas respostas do HTML.
- **Trusted Types**: Habilitar via cabeçalhos CSP e policy no cliente.
  - Report‑Only: adicionar `require-trusted-types-for 'script'; trusted-types foundation-ui` à CSP em `Report-Only` durante 30 dias; logging de violações.
  - Enforce: mover diretivas para CSP principal após período de observação; criar `window.trustedTypes.createPolicy('foundation-ui', { createHTML, createScriptURL })` em `app/providers/security.tsx`.
  - E2E: adicionar verificação de ausência de `TrustedTypePolicyViolation` nos testes após enforcement.
- **Vault Integration**: Quickstart requer `vault kv get foundation/frontend` com chaves `cspNonceSecret`, `trustedTypesPolicy`, `pgcryptoKey`. Exportar em dev como `FOUNDATION_CSP_NONCE`, `FOUNDATION_TRUSTED_TYPES_POLICY`, `FOUNDATION_PGCRYPTO_KEY`. Documentar fallback local e alertas.

## Governance Artifacts

- **ADR Perf-Front**: Registrar em `docs/adr/adr-perf-front.md` (incluído neste plano) com formato ADR padrão (Context → Decision → Consequences). Linkar Art. IX e clarificação de 2025-10-12; justificar Lighthouse+k6; budgets; owners (Frontend Guild + SRE); rollback.
- **Runbook Atualizado**: `docs/runbooks/frontend-foundation.md` (incluído neste plano) contendo: ativação de flags `foundation.fsd`/`design-system.theming`, monitoramento SC-001/SC-005, procedimentos para Chromatic/Lighthouse incidentes, handling de CSP/TT (report-only → enforce), pontos de contato DS Guild.
- **Dashboards & Tags**: Guardar configuração `observabilidade/dashboards/frontend-foundation.json` com widgets LCP, coverage Chromatic, RLS alerts. Garantir tags `@SC-00x` apareçam nas tasks e testes correspondentes. (Stub incluído neste repositório como parte do plano.)
- **Compliance Evidence**: `docs/lgpd/rls-evidence.md` (incluído neste plano) com scripts/fluxos de verificação RLS, checklists LGPD (retenção, direito ao esquecimento) e evidências mínimas para QA.
## Complexity Tracking

*Preencha somente quando algum item da Constitution Check estiver marcado como N/A/violado. Cada linha deve citar explicitamente o artigo impactado e o ADR/clarify que respalda a exceção.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| | | |
