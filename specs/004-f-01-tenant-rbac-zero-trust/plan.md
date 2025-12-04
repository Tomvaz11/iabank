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

## Constitution Check (planejado para tasks)

- [ ] **Art. III - TDD**: criar testes primeiro em `backend/apps/tenancy/tests` e `backend/apps/foundation/tests` (binding `SET LOCAL`, RLS nomeadas, MFA/refresh reuse, ABAC/cache) + Pact/Spectral/oasdiff; gates no CI.
- [ ] **Art. VIII - Lançamento Seguro**: flags/canary, rollback Argo/GitOps, error budget por tenant; checkpoints WORM; owners definidos nas tasks.
- [ ] **Art. IX - Pipeline CI**: cobertura ≥85%, complexidade≤10, SAST/DAST/SCA/SBOM, Spectral/oasdiff/Pact, `scripts/api/check_rate_headers.sh`, k6 auth/ABAC/MFA, `scripts/ci/check-audit-cleanliness.sh`.
- [ ] **Art. XI - Governança de API**: OpenAPI/Pact atualizados (rota→segmento, fingerprints), Problem Details, `RateLimit-*`/`Retry-After`, `Idempotency-Key`, `ETag/If-Match`; tasks alinham codegen e validações.
- [ ] **Art. XIII - Multi-tenant & LGPD**: RLS `CREATE POLICY` default deny, managers tenant-first, middleware HMAC/HKDF + `SET LOCAL`, testes de bypass, pgcrypto e RIPD/ROPA por tenant.
- [ ] **Art. XVIII - Fluxo Spec-Driven**: Sem pendências em `/clarify`; `tasks.md` refletirá gates e evidências WORM/observabilidade.
- Estado: checklist será fechado na fase `/tasks`, com owners tenancy/foundation/contracts/frontend/observabilidade assumindo evidências para cada Artigo.

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

## Fases, Gates e Owners

- **Fase 0 – Contratos/Testes Primeiro**: atualizar OpenAPI/Pact com rota→segmento de rate limit, fingerprints de idempotência, headers obrigatórios; criar testes vermelhos (pytest/DRF + Pact + Spectral/oasdiff) para RLS/binding/ABAC/MFA/refresh/idempotência/rate-limit.
- **Fase 1 – Migrações/RLS/pgcrypto**: migrar Tenant/TenantStateTransition/TenantSecurityProfile/Role/RoleVersion/RoleBinding/SubjectAttribute/IdempotencyKeyRecord/AuthRefreshToken/AuthorizationDecisionLog com expand/contract, RLS default deny (`*_tenant_select/insert/update/delete`), índices tenant-first, pgcrypto em campos sensíveis; scripts SQL versionados.
- **Fase 2 – Middleware/Serviços**: middleware `X-Tenant-Id` + HMAC/HKDF (ordem após auth), binding GUC para Celery/cron (`with_tenant`), rate limiting/idempotência (Redis + Postgres), engine RBAC/ABAC + cache/invalidação, OIDC/SAML + MFA TOTP + refresh chain, WORM publisher.
- **Fase 3 – Observabilidade/Frontend**: métricas/alertas específicos (auth_mfa_latency, abac_eval_latency, rate_limit_hits, idempotency_conflicts, rls_blocked_requests, refresh_reuse_detected), dashboards/alertas, testes e2e front (headers HMAC, Idempotency-Key, If-Match, Problem Details, CSP/TT, PII-free URLs), integração com collectors.
- **Gates CI**: Spectral + oasdiff + Pact; pytest (RLS/ABAC/MFA/refresh/idempotência/rate-limit); k6 auth/ABAC p95<400ms; `scripts/api/check_rate_headers.sh`; `scripts/ci/check-audit-cleanliness.sh`; cobertura ≥85%.
- **Owners**: tenancy (RLS/lifecycle/managers), foundation (auth/MFA/refresh/idempotência/rate limit), contracts (OpenAPI/Pact), frontend (headers/CSP/TT), observabilidade (métricas/alertas/WORM), infra (Terraform/OPA).

## Decisões Detalhadas a Aplicar

### Rate Limiting e Idempotência
- Redis `rl:{segment}:{tenant}` com segmentos `public` 50 rps (burst 2x), `private` 200 rps (burst 2x), `high_risk` multiplicado por `high_risk_multiplier` (default 0.5); falha de Redis em `private/high_risk` → 503 fail-close; `RateLimit-*`/`Retry-After` sempre.
- Mapa rota→segmento: `private` para GET/HEAD/OPTIONS de tenants/roles/bindings/subject-attributes e `GET /auth/refresh` (estado); `high_risk` para mutações (criar/patch/transicionar tenant, roles/versions/bindings/subject-attributes, auth token/refresh/revoke, uploads ABAC); `public` apenas health/discovery se exposto.
- Idempotência: Redis + Postgres (RLS) com `idempotency_key`, `key_hash`, `payload_hash`, `tenant_id`, `endpoint`, `response_snapshot`, `expires_at` (24h); replays iguais retornam resposta, divergentes → 409/422; GC via cron/beat.
- Fingerprints: `POST /tenants` hash `method+path+{slug,allowed_domains,idp_metadata,contacts,risk_classification,region,retention_policy}`; `PATCH/transition tenants` inclui `If-Match`; roles/bindings/subject-attributes `method+path+sorted(body)` (+ `If-Match` se houver); `POST /auth/token` `tenant_id+hash(idp_assertion)+hash(device_fp|ua)+mfa_level`; `POST /auth/refresh|/revoke` `tenant_id+session_id+hash(refresh_token HMAC)`.

### Identidade, MFA e Refresh
- OIDC: `mozilla-django-oidc` (Auth Code + PKCE); SAML: `python3-saml` com `idp_metadata` cifrado via pgcrypto por tenant; MFA TOTP: `django-otp`/`django-otp-totp` (segredo cifrado).
- Refresh opaco `AuthRefreshToken` (hash HMAC-SHA256, `session_id`, status `active|rotated|revoked|reused`, `replaced_by`, `fingerprint_hash`, `ip_masked`, `expires_at`); cookie `HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh`.
- Reuse detection: cada uso gera novo ativo, anterior vira `rotated`; se token antigo reaparece, marca `reused`, revoga cadeia por `session_id`, grava WORM e alerta. `suspended` bloqueia emissão/refresh; `blocked` revoga e nega tudo.

### Binding Multi-tenant e RLS
- Middleware `X-Tenant-Id` + `X-Tenant-Signature` (HMAC HKDF por tenant) compara com sessão/claim, seta GUC `iabank.tenant_id` antes de qualquer query; ordem: após auth, antes de acesso a DB.
- Helpers `with_tenant` para Celery/cron/shell setarem GUC e ContextVar; testes de bypass (header/body/path) garantem `SET LOCAL` e RLS bloqueando cross-tenant.
- RLS nomeadas `*_tenant_select/insert/update/delete` default deny, aplicadas a todas as tabelas novas e existentes com `tenant_id`.
- Migrações expand/contract: (1) criar tabelas/colunas novas com defaults e RLS desabilitada; (2) preencher dados/ajustes de nullability; (3) criar índices únicos por tenant (`tenant_id, slug/display_name/...`) `CONCURRENTLY`; (4) habilitar RLS e políticas USING/WITH CHECK por operação com `tenant_id = current_setting('iabank.tenant_id')::uuid`; (5) VALIDATE CONSTRAINT/FOREIGN KEY; (6) remover colunas legadas. Pgcrypto em `Tenant.idp_metadata`, contatos (`security_contacts`, `ops_contacts`), segredos MFA (`django-otp`), device/user-agent fingerprints; colunas auxiliares de hash (`*_hash`) para unicidade e busca sem expor PII (ex.: `contact_email_hash`, `device_fingerprint_hash`).

### RBAC/ABAC
- Permissions no formato `resource:action`; serviço `abac.py` valida `configs/abac/tenant-policy.schema.json`, cache Redis `abac:{tenant}:{role}:{policy_version}`, invalidação em RoleVersion/RoleBinding/SubjectAttribute, registro em `AuthorizationDecisionLog` (mascarado).
- DRF permission class combinando RBAC+ABAC; testes object-level allow/deny e cache miss/mismatch.

### WORM e Auditoria
- Payload mínimo: tipo (tenant_transition|role_version|auth_refresh_reuse|abac_denied), tenant_id, actor_id, trace/span, etag_before/after, status, hash. Assinatura SHA-256 + KMS/Vault, verificação pós-upload (fail-close), retenção ≥365d.
- Publisher dedicado para eventos críticos; falha de upload → 503 e rollback da mutação.

### Observabilidade e SLO
- Buckets WORM e telemetria: `worm-f01-{env}` com retenção dev/stage 365d e prod 730d; ingestão só com checksum SHA-256 + assinatura KMS/Vault (hex) e verificação pós-upload (fail-close). Logs/spans métricos exportam `pii_redacted=true`; se collector falhar → aborta mutação crítica.
- Métricas/spans nomeadas: `auth_mfa_latency` (p95<=400ms, p99<=600ms), `abac_eval_latency` (p95<=400ms), `rate_limit_hits` (labels segment/tenant), `idempotency_conflicts`, `rls_blocked_requests`, `refresh_reuse_detected`, `worm_upload_failures`, `error_budget_burn`. Alertas: p95 acima do alvo por 5m; `refresh_reuse_detected>0`; 403/404 cross-tenant spike; 412/429 acima de limiar; falha de verificação WORM >0.
- Dashboards/alertas alinhados a OTEL/Prometheus; error budget por tenant 0.5% mensal com auditoria de queima e ação de redução de blast radius.

### Frontend
- Interceptors sempre com `X-Tenant-Id`, assinatura HMAC quando aplicável, `traceparent/tracestate`, `Idempotency-Key` em mutações, `If-Match` onde exigido; CSP strict-dynamic + Trusted Types (fallback documentado) e2e cobrindo Problem Details e ausência de PII em URLs.
- Mapeamento de páginas/requests: onboarding de tenant (create/transition) e gestão de segurança usam `X-Tenant-Id`+assinatura e `Idempotency-Key`; gestão de roles/versions/bindings usa `If-Match` e Idempotency-Key; auth token/refresh/revoke usa Idempotency-Key e fingerprint de device (hash lado cliente) sem PII em URL; telas de leitura usam apenas `X-Tenant-Id`. Cache TanStack Query: chaves `['tenant', ...]`, `resetOnTenantChange=true`, invalidação de mutações por tenant; desabilitar cache para mutações `high_risk` e revalidar após 201/204. CSP/Trusted Types: nonce por request, policy única (`iabankPolicy`), nenhum inline script/style sem nonce, quedas de Trusted Types caem para sanitização reforçada.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Nenhuma violação planejada | Mantemos simplicidade e aderência à Constituição |
