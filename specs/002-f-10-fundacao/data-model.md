# Data Model — F-10 Fundação Frontend FSD e UI Compartilhada

## Overview

O foco desta fundação é garantir isolamento multi-tenant, governança de design system e contratos FE/BE. As entidades abaixo abrangem tanto estruturas persistidas (backend/PostgreSQL) quanto artefatos versionados no monorepo, respeitando Art. I, XI, XIII da constituição e as diretrizes de `BLUEPRINT_ARQUITETURAL.md §4`.

## Entities

### Tenant
- **Descrição**: Representa um espaço lógico isolado (cliente/linha de negócio) usado em todo o monorepo para RLS, roteamento e branding.
- **Campos**:
  - `id` (UUID, PK) — chave interna utilizada por RLS.
  - `slug` (string, <= 32, único) — identifica o tenant em subdomínios (`{slug}.iabank.com`).
  - `display_name` (string, <= 128) — nome público.
  - `primary_domain` (string, <= 255, único) — domínio de produção principal.
  - `status` (enum: `pilot`, `production`, `decommissioned`) — controla rollout e error budgets.
  - `pii_policy_version` (string, SemVer) — vincula à política LGPD vigente (mascaramento, retenção).
  - `default_theme_id` (UUID, FK → TenantThemeToken.id) — tema padrão aplicado ao login.
  - `created_at` / `updated_at` (timestamp with time zone).
- **Relações**:
  - 1:N com `TenantThemeToken` (variações de tema).
  - 1:N com `FeatureTemplateRegistration` (registro de scaffolding aplicado).
- **Validações**:
  - `slug` deve ser `^[a-z0-9-]+$`.
  - `primary_domain` deve ser domínio válido e exclusivo.
- **Regras**:
  - RLS garante acesso apenas ao tenant logado (`tenant_id = current_setting('app.tenant_id')`).
  - `status=decommissioned` impede novas features até migração concluída.
- **Implementação**:
  - Localizado em `backend/apps/tenancy/models/tenant.py` (já existente).
  - Migração `backend/apps/tenancy/migrations/0025_enable_rls_frontend.py` adiciona `pii_policy_version` e integra RLS.
  - Managers atualizados em `backend/apps/tenancy/managers.py` para incluir escopo automático.

### TenantThemeToken
- **Descrição**: Catálogo versionado de tokens Tailwind + CSS vars por tenant.
- **Campos**:
  - `id` (UUID, PK).
  - `tenant_id` (UUID, FK → Tenant.id).
  - `version` (string, SemVer) — sincronizado com `docs/design-system/tokens.md`.
  - `category` (enum: `foundation`, `semantic`, `component`).
  - `json_payload` (JSONB) — mapa de tokens (`token_name -> value`); criptografado para valores sensíveis (ex.: logos base64).
  - `wcag_report` (JSONB, opcional) — snapshot de auditoria (contraste, status).
  - `chromatic_snapshot_id` (string, opcional) — referência ao build Chromatic.
  - `is_default` (boolean) — indica tema aplicado automaticamente.
  - `created_at` (timestamp with time zone).
- **Relações**:
  - Pertence a `Tenant`; referenciado por `DesignSystemStory`.
- **Validações**:
  - `json_payload` deve seguir schema validado por zod (`TokenSchema`).
  - `wcag_report` obrigatório quando `category != foundation`.
- **Regras**:
  - Atualizações exigem pipeline Chromatic e validação WCAG antes de `is_default = true`.
  - Eventos de mudança disparam job Celery para regenerar `tokens.css`.
- **Implementação**:
  - Novo modelo em `backend/apps/tenancy/models/tenant_theme_token.py`.
  - Manager `TenantThemeTokenManager` injeta `tenant_id` e aplica `pgcrypto` (coluna `json_payload` com função `pgp_sym_encrypt`).
  - Serializer `TenantThemeSerializer` em `backend/apps/foundation/serializers/theme.py`.
  - Migração `0001_frontend_foundation_expand.py` cria tabela, chama `CREATE POLICY` e habilita `ENABLE ROW LEVEL SECURITY`.

### FeatureTemplateRegistration
- **Descrição**: Registro idempotente do scaffolding aplicado para cada feature FSD por tenant.
- **Campos**:
  - `id` (UUID, PK).
  - `tenant_id` (UUID, FK → Tenant.id).
  - `feature_slug` (string, <= 64) — nome normalizado (`loan-tracking`).
  - `slice` (enum: `app`, `pages`, `features`, `entities`, `shared`) — última camada inicializada.
  - `scaffold_manifest` (JSONB) — arquivos gerados (paths, hashes).
  - `created_by` (UUID FK → User.id) — Tech Lead responsável.
  - `duration_ms` (integer) — tempo de execução do scaffolding (feed SC-001).
  - `created_at` (timestamp with time zone).
- **Relações**:
  - 1:N com `FeatureTemplateMetric`.
- **Validações**:
  - `feature_slug` único por tenant.
  - `scaffold_manifest` deve incluir entradas para `api`, `model`, `ui`, `tests`.
- **Regras**:
  - Registros só podem ser criados via endpoint protegido com `Idempotency-Key`.
  - Atualizações posteriores apenas para `slice` quando scaffolding incremental completar camadas faltantes.
- **Implementação**:
  - Modelo em `backend/apps/foundation/models/feature_template_registration.py`.
  - Manager `FeatureTemplateRegistrationManager` aplica `select_for_update` em conjunto com idempotência (residente em `backend/apps/foundation/managers.py`).
  - Serviço `ScaffoldRegistrar` (`backend/apps/foundation/services/scaffold_registrar.py`) orquestra validações, gera métricas.
  - Migração `0002_frontend_foundation_backfill.py` migra dados legados e popula registros iniciais.

### FeatureTemplateMetric
- **Descrição**: Métricas de pós-scaffolding vinculadas às histórias/SC do spec.
- **Campos**:
  - `id` (UUID, PK).
  - `registration_id` (UUID, FK → FeatureTemplateRegistration.id).
  - `metric_code` (enum: `SC-001`, `SC-002`, `SC-003`, `SC-004`, `SC-005`).
  - `value` (numeric) — resultado da medição (ex.: % cobertura visual).
  - `collected_at` (timestamp with time zone).
  - `source` (enum: `ci`, `chromatic`, `lighthouse`, `manual`).
- **Validações**:
  - `value` para `SC-002` deve ser 0-100; `SC-001` em minutos (< 60 p95).
  - Unicidade composta recomendada: `tenant_id` + `registration_id` + `metric_code` + `collected_at` (evita colisões entre tenants/features).
- **Regras**:
  - CI publica métricas via webhook autenticado; falhas disparam alerta de budget.
- **Implementação**:
  - Modelo em `backend/apps/foundation/models/feature_template_metric.py`.
  - Endpoint `TenantMetricViewSet` agrega e exponibiliza via serializer `SuccessMetricSerializer`.
  - Worker Celery `foundation/tasks/publish_metrics.py` injeta registros a partir de pipelines.

### DesignSystemStory
- **Descrição**: Representa um componente UI em Storybook com variações multi-tenant e metadados de acessibilidade.
- **Campos**:
  - `id` (UUID, PK).
  - `component_id` (string) — caminho FSD (`shared/ui/button`).
  - `tenant_id` (UUID FK → Tenant.id) ou `null` para tema default.
  - `story_id` (string) — nome da story (`Primary`, `Skeleton`).
  - `chromatic_build` (string) — identificador do build.
  - `axe_results` (JSONB) — relatórios de acessibilidade (violations, passes).
  - `coverage_percent` (numeric) — percentual de estados cobertos.
  - `storybook_url` (string) — link para a story publicada.
  - `updated_at` (timestamp with time zone).
- **Validações**:
  - `coverage_percent` >= 95 para componentes críticos.
  - `axe_results.violations` deve ser lista vazia para status aprovado.
- **Regras**:
  - Builds com `axe_results` não vazios bloqueiam merge (fail-closed).
- **Implementação**:
  - Modelo em `backend/apps/foundation/models/design_system_story.py`.
  - Sincronização via webhook Chromatic → endpoint `DesignSystemStoryViewSet.ingest`.
  - Script `scripts/chromatic/webhook_handler.py` normaliza payload, mascara dados sensíveis.

### ApiContractArtifact
- **Descrição**: Artefato versionado que representa contratos OpenAPI/Pact e seus estados.
- **Campos**:
  - `id` (UUID, PK).
  - `type` (enum: `openapi`, `pact-consumer`, `pact-provider`).
  - `version` (string, SemVer).
  - `checksum` (string, SHA-256) — garante integridade.
  - `path` (string) — caminho no monorepo (`contracts/api.yaml`).
  - `breaking_change` (boolean).
  - `released_at` (timestamp with time zone, opcional) — quando aplicado em produção.
- **Relações**:
  - 1:N com `ContractDiffReport`.
- **Regras**:
  - Atualização de `openapi` obriga novo `pact-consumer` se breaking ou se recurso monitorado.
  - `breaking_change=true` exige UI fallback ou feature flag antes do merge (Art. XI, VIII).
- **Implementação**:
  - Modelo existente em `backend/apps/contracts/models.py` será estendido com campos `breaking_change` e `released_at`.
  - Signals em `backend/apps/contracts/signals.py` disparam lint/diff e registram `ContractDiffReport`.

### ContractDiffReport
- **Descrição**: Resultado do lint/diff executado no pipeline, armazenado para auditoria.
- **Campos**:
  - `id` (UUID, PK).
  - `artifact_id` (UUID, FK → ApiContractArtifact.id).
  - `tool` (enum: `spectral`, `oasdiff`, `pact-cli`).
  - `status` (enum: `pass`, `warn`, `fail`).
  - `summary` (text) — itens relevantes (ex.: campos adicionados).
  - `logged_at` (timestamp with time zone).
- **Regras**:
  - `status=fail` impede publicação até que um artifact atualizado seja anexado.
- **Implementação**:
  - Criado em `backend/apps/contracts/models.py` (classe nova).
  - Persistido via workflow GitHub Actions (job `contracts`) chamando endpoint `POST /contracts/diff-reports`.
  - Visualização planejada em dashboard `observabilidade/dashboards/frontend-foundation.json`.

## Relationships Diagram (textual)

- `Tenant` 1 — N `TenantThemeToken`
- `Tenant` 1 — N `FeatureTemplateRegistration`
- `FeatureTemplateRegistration` 1 — N `FeatureTemplateMetric`
- `TenantThemeToken` 1 — N `DesignSystemStory` (por tema)
- `ApiContractArtifact` 1 — N `ContractDiffReport`

## State Transitions

- **TenantThemeToken**: `draft` (Chromatic em execução) → `validated` (Chromatic + WCAG ok) → `active` (is_default true). Transição para `active` dispara deploy via Argo CD e invalida caches TanStack Query (`tenantTheme` key).
- **FeatureTemplateRegistration**: `initiated` → `linted` → `tested` → `published`. Cada transição é condicionada a gates (`linted`: ESLint/TS pass; `tested`: Vitest & Pact; `published`: Chromatic + Lighthouse budgets).
- **ApiContractArtifact**: `proposed` → `validated` (Spectral, Pact pass) → `released` (deploy concluído). Breaking changes exigem `feature flag` ativa até `released`.

## Validation Rules Summary

- Todas as entidades com `tenant_id` obedecem RLS e managers que aplicam filtro automático.
- Campos com PII (`primary_domain`, `display_name`) são mascarados em logs (Art. XII).
- JSON payloads validam contra schemas Zod/YAML publicados em `docs/design-system/tokens.md`.
- `Idempotency-Key` obrigatório para criação de `FeatureTemplateRegistration`.
- Serviços HTTP devem anexar `traceparent` e `tracestate`; testes garantem correlação OTEL front/back.

## Notes

- Dados sensíveis em `TenantThemeToken.json_payload` utilizam `pgcrypto` (AES-GCM) conforme ADR-010.
- Métricas SC alimentam dashboards SLO via Exporters (Prometheus → Grafana).
- Todos os artifacts possuem rastreabilidade com tags `@SC-00x` nos pipelines e PRs, conforme sucesso criterias do spec.
- Migrações seguem padrão expand/contract documentado em `docs/runbooks/frontend-foundation.md`; scripts SQL revisados por DBA antes do deploy.
