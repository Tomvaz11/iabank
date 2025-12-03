# Implementation Plan: Governanca de Tenants e RBAC Zero-Trust

**Branch**: `004-f-01-tenant-rbac-zero-trust` | **Date**: 2025-12-03 | **Spec**: /home/pizzaplanet/meus_projetos/iabank/specs/004-f-01-tenant-rbac-zero-trust/spec.md  
**Input**: Feature specification from `/specs/004-f-01-tenant-rbac-zero-trust/spec.md`

## Summary

Entregar isolamento zero-trust multi-tenant com Django 4.2/DRF 3.15 sobre PostgreSQL 15 (RLS por `CREATE POLICY` + `SET LOCAL`), governando lifecycle de tenants, RBAC+ABAC versionado e MFA/refresh seguro, conforme spec `/specs/004-f-01-tenant-rbac-zero-trust/spec.md` e Constituicao (Arts. I, III, XI, XIII, XVIII). O frontend React/Vite consumira APIs `/api/v1` contract-first (OpenAPI 3.1/Problem Details/Pact) com rate limiting, idempotencia e auditoria WORM (Object Lock). Art. XII e ADR-010/011/012 guiam protecao de PII (pgcrypto), CSP/Trusted Types e mascaramento em telemetria.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.6/Node.js 20 (contracts/tools)  
**Primary Dependencies**: Django 4.2, DRF 3.15, Celery 5.3, Redis 7, pgcrypto, factory-boy, structlog, OpenTelemetry SDK, django-prometheus, Sentry, Spectral/oasdiff/Pact  
**Storage**: PostgreSQL 15 com RLS via `CREATE POLICY` e `SET LOCAL iabank.tenant_id`; Redis para rate limiting/locks/idempotencia  
**Testing**: pytest + factory-boy + cliente DRF; testes de contrato (Spectral/oasdiff/Pact); k6 para carga; ruff/coverage>=85% (Art. III/IX)  
**Target Platform**: Linux containers/orquestrador com GitOps (Argo CD)  
**Project Type**: Monolito modular web (Django/DRF + React/Vite)  
**Performance Goals**: Autorizacao/MFA p95 < 400 ms; conflitos `If-Match` resolvidos < 1s; rate limit público 50 rps, privado 200 rps (alto risco 50%)  
**Constraints**: TDD obrigatório; expand/contract em migrações (Art. X); proibição de service accounts; tokens com HttpOnly/Secure/SameSite=Strict; cobertura >=85%; RLS ininterrupta; Problem Details RFC 9457; WORM retenção >=365d  
**Scale/Scope**: Multi-tenant B2B; onboarding/gestao de tenants, roles e auditoria; integra IdP externo OIDC/SAML com MFA obrigatória

### Contexto Expandido

**Backend**: Django 4.2/DRF 3.15 (Art. I) em monolito modular; app de tenancy centraliza managers/querysets tenant-first, middleware `X-Tenant-Id` com HMAC-SHA256/HKDF (Vault/KMS) usando salt/version por tenant, binding `SET LOCAL`, pgcrypto para PII; ausência/divergência de assinatura retorna Problem Details 403/404 e não muda o `tenant_id` da sessão; Celery 5.3 + Redis para tarefas/locks (rate limit deduplicacao/idempotencia); versionamento de modelos via django-simple-history; políticas RLS nomeadas por operação (`*_tenant_select/insert/update/delete`) default deny `tenant_id = current_setting('iabank.tenant_id')::uuid`.  
**Frontend**: React 18 + Vite (FSD), TanStack Query, Zustand; consumo de `/api/v1` com headers de rastreamento (`Traceparent`, `RateLimit-*`, `Idempotency-Key`, `If-Match`), CSP strict-dynamic e Trusted Types (Art. XII); nonce gerado por request e aplicado a scripts/style, fallback documentado para ambientes sem Trusted Types com sanitização reforçada e testes e2e de sinks críticos, proibição de PII em URLs/telemetria.  
**Async/Infra**: Redis 7 (broker Celery + cache rate limiting/idempotencia), k6 para carga; IaC Terraform + GitOps Argo CD com políticas OPA para RLS/rate limit/WORM (Art. XIV) em `infra/terraform` e `infra/opa/*`, aplicadas por Argo apps com drift/rollback e janela off-peak.  
**Persistência/Dados**: PostgreSQL 15 com RLS versionada (CREATE POLICY), índices tenant-first, unicidade por tenant, pgcrypto para campos PII; WORM em S3 Object Lock para auditoria com verificação de hash/assinatura (eventos: transição de tenant, RoleVersion publish/rollback, reuse/rotação de refresh, mudança de TenantSecurityProfile, negativas ABAC críticas); políticas de retenção e direito ao esquecimento pós-365d. Idempotência híbrida: dedupe rápida em Redis (`idemp:{tenant}:{env}:{hash(key)}` TTL 24h) com trilha/auditoria em Postgres sob RLS.  
**Testing Detalhado**: TDD/integracao-primeiro (Art. III/IV) com pytest + DRF client + factory-boy; suites de contrato (OpenAPI 3.1 lint/diff Spectral/oasdiff, Pact), testes de autorizacao RBAC+ABAC versionado, testes de RLS bypass, k6 para p95/p99, coverage>=85% e complexidade<=10 (Art. IX).  
**Observabilidade**: OpenTelemetry + structlog + django-prometheus + Sentry (Art. VII/ADR-012) com mascaramento de PII, spans/logs/metricas com `tenant_id`, `role_id`, `role_version`, decisão ABAC (`allow|deny`), `policy_version`, resultado MFA, `trace_id/span_id`, `pii_redacted=true`; dashboards por tenant e alertas de reuse de refresh token e 42x/429; export falho → fail-close.  
**Segurança/Compliance**: OWASP ASVS/NIST SSDF (Art. XII), MFA TOTP obrigatória, ban a service accounts; RBAC+ABAC por tenant com baseline de atributos (unidade/classificacao/regiao/tipo de recurso); HMAC-SHA256 do `X-Tenant-Id` com HKDF por tenant, rotação 90d, chave raiz em Vault/KMS; rate limiting per-tenant e Idempotency-Key TTL 24h com deduplicacao auditavel; Problem Details RFC 9457; LGPD (ROPA/RIPD) e auditoria WORM (Art. XIII/XVI).  
**Segurança/Compliance (tokens/ABAC)**: Refresh tokens opacos em Postgres com RLS (`auth_refresh_token` com hash HMAC-SHA256, status `active|rotated|revoked|reused`, cadeia por `session_id`, expiração padrão 7d, rotação a cada uso, reuse detection e revogação em cascata), cache Redis curto (15 min) para status; sempre emitidos via cookie `HttpOnly; Secure; SameSite=Strict`. ABAC validado por JSON Schema 2020-12 (`configs/abac/tenant-policy.schema.json`) parametrizável por tenant (catálogos declarados no próprio schema), com `policy_version` e `policy_checksum` (SHA-256); cache Redis `abac:{tenant}:{role}:{policy_version}` TTL curto e invalidação em mismatch/atualização; avaliação falha fechado com Problem Details e auditoria. Role bindings normalizados (`RoleBinding` + `SubjectAttribute`) são fonte de verdade para sujeitos/atributos.

**RLS/pgcrypto (alvos de governança)**: aplicar políticas nomeadas `*_tenant_select/insert/update/delete` (default deny `tenant_id = current_setting('iabank.tenant_id')::uuid`) em: Tenant, TenantStateTransition, TenantSecurityProfile, Role, RoleVersion, RoleBinding, SubjectAttribute, IdempotencyKeyRecord (trilha), AuthRefreshToken (status), e tabelas já existentes de seeds/fundação com `tenant_id`. Criptografar com pgcrypto campos sensíveis (`idp_metadata`, contatos, device_fp, segredos MFA) e usar hashes auxiliares para unicidade quando necessário.
**Performance Targets**: p95<400ms para auth/ABAC/MFA; RLS sem regressão de latência; rate limit público 50 rps (burst 2x), privado 200 rps (burst 2x), alto risco 50%; rollback roles/tenant <10 min; MTTR <30 min para falhas de isolamento; k6 para auth/ABAC/MFA com thresholds p95/p99 (script em `observabilidade/k6/auth-abac.js`).  
**Restrições Operacionais**: Fluxo Spec-Driven (Art. XVIII); controle de concorrencia via `ETag/If-Match`; Idempotency-Key obrigatória em mutações; expand/contract preservando RLS; WORM não pode ser desativado; tokens em cookie HttpOnly/Secure/SameSite=Strict; headers `RateLimit-*`/`Retry-After` em GET/POST; evidências WORM assinadas e verificadas pós-upload.  
**Escopo/Impacto**: Apps `backend/apps/tenancy` (gestao tenant, RLS, managers), `backend/apps/foundation` (auth/MFA/SSO), `backend/apps/contracts` (OpenAPI/Pact), `frontend` (consumo seguro), `observabilidade` (dashboards); integração com Vault/KMS para HMAC, Redis para rate limit; nenhum `[NEEDS CLARIFICATION]` pendente.

## Constitution Check

- [ ] **Art. III - TDD**: Planejar primeiros testes em `/home/pizzaplanet/meus_projetos/iabank/backend/apps/tenancy/tests` e `/home/pizzaplanet/meus_projetos/iabank/backend/apps/foundation/tests` cobrindo binding `SET LOCAL`, políticas RLS nomeadas (SELECT/INSERT/UPDATE/DELETE), MFA/refresh (rotação/reuse) e ABAC schema/cache antes de código.  
- [ ] **Art. VIII - Lancamento Seguro**: Feature flags/canary via `backend/apps/tenancy/feature_flags.py`, rollback versionado de roles/tenant e monitoramento de error budget por tenant; flag para rotas auth/ABAC, rollback Argo/GitOps, checkpoints WORM.  
- [ ] **Art. IX - Pipeline CI**: Cobertura >=85%, complexidade<=10, SAST/DAST/SCA/SBOM, lint/diff OpenAPI/Pact, `scripts/api/check_rate_headers.sh`, k6 para auth/ABAC/MFA; `scripts/ci/check-audit-cleanliness.sh` para logs/WORM e PII; referenciar `Makefile`/CI existentes.  
- [ ] **Art. XI - Governanca de API**: Contratos `/api/v1` em `/home/pizzaplanet/meus_projetos/iabank/specs/004-f-01-tenant-rbac-zero-trust/contracts/`, Spectral/oasdiff, Pact, erros RFC 9457, versionamento `/api/v1`, `RateLimit-*`/`Retry-After` em GET/POST, `Idempotency-Key` em mutações, `ETag/If-Match` em recursos versionados.  
- [ ] **Art. XIII - Multi-tenant & LGPD**: RLS com `CREATE POLICY` nomeadas e default deny `tenant_id = current_setting('iabank.tenant_id')::uuid`, managers tenant-first, middleware `X-Tenant-Id` validando HMAC/HKDF (salt por tenant) e `SET LOCAL`, testes de bypass e RIPD/ROPA por tenant.  
- [ ] **Art. XVIII - Fluxo Spec-Driven**: Artefatos `/specs/004-f-01-tenant-rbac-zero-trust/` alinhados; pendencias em `/clarify` se surgirem; `tasks.md` refletirá estes gates e evidências WORM/observabilidade.

## Project Structure

### Documentacao (esta feature)

/home/pizzaplanet/meus_projetos/iabank/specs/004-f-01-tenant-rbac-zero-trust/  
|-- plan.md (este plano, fase 0/1)  
|-- research.md (decisoes de pesquisa fase 0)  
|-- data-model.md (modelo de dados e estados)  
|-- quickstart.md (como exercitar contratos/testes)  
`-- contracts/ (OpenAPI 3.1/Pact gerados na fase 1)

### Codigo-Fonte (repositorio)

- /home/pizzaplanet/meus_projetos/iabank/backend/apps/tenancy: RLS, lifecycle de tenant, managers/querysets tenant-first, middleware/binding `SET LOCAL`, Idempotency-Key/rate limiting (Art. I/II/XIII).  
- /home/pizzaplanet/meus_projetos/iabank/backend/apps/foundation: Autenticacao OIDC/SAML, MFA TOTP, refresh tokens HttpOnly/Secure/SameSite=Strict (Art. I/II/XII).  
- /home/pizzaplanet/meus_projetos/iabank/backend/apps/contracts: Governanca de OpenAPI/Pact e Problem Details (Art. XI).  
- /home/pizzaplanet/meus_projetos/iabank/backend/config: Configuração de middleware, settings de RLS/pgcrypto, integrações Vault/Redis/Sentry/OTel (Art. I/VII/XIII).  
- /home/pizzaplanet/meus_projetos/iabank/frontend: Consumo dos contratos `/api/v1` com cabeçalhos de rastreamento/idempotencia e CSP/Trusted Types (Art. I/XII).  
- /home/pizzaplanet/meus_projetos/iabank/observabilidade: Dashboards/alertas por tenant (Art. VII/XVI).  
- /home/pizzaplanet/meus_projetos/iabank/infra: IaC Terraform + políticas OPA/GitOps para RLS/rate limiting/WORM (Art. XIV).  
- /home/pizzaplanet/meus_projetos/iabank/scripts: Scripts de lint/diff (Spectral/oasdiff), verificação de commit/SC-tag e automações de pipeline (Art. IX/XI/XVIII).

**Structure Decision**: Mantemos monolito modular com apps dedicados (Art. I/II), evitando novos módulos ao reutilizar `backend/apps/tenancy` e `backend/apps/foundation` como SSOT para isolamento/autenticação; contratos ficam em `backend/apps/contracts` para alinhar fluxo contrato-primeiro. Infra/observabilidade/front apenas recebem ajustes para headers e políticas, sem violar simplicidade.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| | | |
