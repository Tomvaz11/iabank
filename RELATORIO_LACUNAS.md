# Relatório de Lacunas — Governança de Tenants e RBAC Zero-Trust

Formato das tags de resolução:
- `[EXISTENTE]` já coberto em artefatos normativos/codebase.
- `[NOVA]` decisão sugerida com base nos artefatos existentes.
- `[PARCIAL]` parte coberta, parte proposta como nova decisão.

1) Inventário/ordem de RLS para novas tabelas  
Tag: [PARCIAL]  
Lacuna: lista incompleta de tabelas com RLS (apenas legado em `backend/apps/tenancy/sql/rls_policies.sql`, GUC divergente).  
Decisão: criar inventário explícito e ordenado para `tenant`, `tenant_state_transition`, `tenant_security_profile`, `role`, `role_version`, `role_binding`, `subject_attribute`, `idempotency_key_record`, `authorization_decision_log`, `auth_refresh_token`; usar GUC `iabank.tenant_id`. Migração expand/contract: criar tabelas com RLS off → backfill/índices CONCURRENTLY → habilitar RLS/políticas `*_tenant_select/insert/update/delete` default deny → validar constraints. Incluir testes `\dRp+` e checagem de GUC.

2) Divergência AuthRefreshToken vs RefreshToken  
Tag: [NOVA]  
Lacuna: nomenclatura e modelo divergentes (plan vs data-model) e ausência de fonte de verdade.  
Decisão: fixar modelo `AuthRefreshToken` com colunas `id`, `tenant_id` FK, `user_id` FK, `session_id`, `token_hash` (HMAC-SHA256), `status` (`active|rotated|revoked|reused`), `replaced_by` FK self, `fingerprint_hash`, `ip_masked`, `expires_at`, `issued_at`, `last_used_at`, `mfa_level`; RLS por `tenant_id`; pgcrypto só onde necessário (fingerprint). Alinhar data-model/plan e remover “RefreshToken” duplicado.

3) Invariantes/FKs RoleVersion × RoleBinding × SubjectAttribute  
Tag: [NOVA]  
Lacuna: ausência de unicidades/FKs/cache no data-model.  
Decisão: `RoleVersion` UNIQUE `(role_id, version)`; `RoleBinding` FK para `RoleVersion` (ou par `role_id+version`) e UNIQUE `(tenant_id, subject_id, role_version_id)`; `SubjectAttribute` UNIQUE `(tenant_id, subject_id, key)` limitado ao schema ABAC. Invalidação de cache `abac:{tenant}:{role}:{policy_version}` em mudanças de versão/atributos. Testes object-level allow/deny cobrindo cache hit/miss.

4) Estrutura do IdempotencyKeyRecord (fingerprint/snapshot/índices/GC)  
Tag: [PARCIAL]  
Lacuna: faltam campos/índices/política de GC para o registro geral (além do padrão de seeds).  
Decisão: tabela com `id`, `tenant_id`, `endpoint`, `idempotency_key` (VARCHAR 128, UNIQUE por tenant+endpoint), `key_hash`, `payload_hash`, `response_snapshot` (JSONB, máx. ~16KB), `status` (`pending|completed|failed`), `response_code`, `expires_at` (default now+24h), `created_at`; índices `(tenant_id, endpoint)` e `(tenant_id, key_hash)`; GC via Celery beat; cache `idemp:{tenant}:{endpoint}:{key_hash}` com TTL alinhado; replay igual retorna snapshot, divergente → 409/422. Atualizar plan/data-model.

5) Publisher WORM para eventos da feature  
Tag: [PARCIAL]  
Lacuna: só há fluxo WORM completo para seeds; faltam parâmetros/eventos para tenant/roles/auth.  
Decisão: reutilizar padrão seed-data com S3 Object Lock (Compliance) `worm-tenant-rbac-{env}`, KMS por ambiente, timeout 10s + retries exponenciais (3). Eventos mínimos: `tenant_transition`, `role_version_publish|rollback`, `auth_refresh_reuse`, `abac_denied_critical`, `idempotency_conflict_high_risk`. Fail-close em upload/verificação; checklist obrigatório (PII masked, RLS ok, idempotência ok, headers RateLimit/ETag). Retenção ≥365d. Documentar no plan/quickstart.

6) Fronteiras/dependências da Fase 2  
Tag: [NOVA]  
Lacuna: Fase 2 genérica, sem ordem/boundaries.  
Decisão: fatiar e ordenar com critérios de pronto:  
  1. Middleware binding `X-Tenant-Id` + GUC + managers tenant-first (inclui `with_tenant` para Celery/cron).  
  2. RLS/índices/migrações das novas tabelas (inventário explícito) + validações.  
  3. Idempotência (Redis+Postgres) + Rate limiting por segmento com headers.  
  4. Engine RBAC+ABAC + cache/invalidação + schema por tenant.  
  5. OIDC/SAML + MFA TOTP + cadeia de `AuthRefreshToken`/reuse.  
  6. Publisher WORM integrado a eventos críticos.  
  7. APIs `/api/v1` com Problem Details/ETag/If-Match/Idempotency-Key.  
  8. Observabilidade (OTEL/structlog/prometheus/Sentry) com labels obrigatórias.

7) Rotação/uso de HMAC por tenant (TenantSecurityProfile)  
Tag: [PARCIAL]  
Lacuna: política existe em runbooks, mas não amarrada ao profile/backend.  
Decisão: `TenantSecurityProfile` mantém `hmac_key_version`, `hmac_salt_version`, `rotates_at`. Middleware consulta cache `hmac:{tenant}:{version}`; rotação com `grace_period` (p.ex. 24h) e invalidação de cache; auditoria WORM registra `tenant_id`, versões antiga/nova, `rotates_at`. Passos: atualizar Vault/KMS, persistir no profile, invalidar cache, smoke test de binding.

8) Mapeamento frontend (telas/rotas, headers, CSP/TT, Problem Details)  
Tag: [PARCIAL]  
Lacuna: faltam páginas/rotas específicas da feature e validações e2e.  
Decisão: mapear em plan/quickstart:  
  - Onboarding/gestão de tenant (`features/tenants`): `X-Tenant-Id` + assinatura, `Idempotency-Key`, `If-Match` em transições; exibir Problem Details/RateLimit/Retry-After.  
  - Roles/versions/bindings/subject-attributes (`features/roles`): `Idempotency-Key` em mutações, `If-Match` em PATCH/publish, tratamento de 409/412.  
  - Auth token/refresh/revoke (`features/auth`): `Idempotency-Key`, hash de fingerprint no cliente, cookies HttpOnly/Secure/SameSite=Strict.  
  - Leituras: apenas `X-Tenant-Id` + assinatura; PII fora de URLs.  
  - Query keys sempre incluem `tenant_id` (`['tenant', tenantId, ...]`); e2e validam CSP/Trusted Types, headers obrigatórios e Problem Details renderizados.
