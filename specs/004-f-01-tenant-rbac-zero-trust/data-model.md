# Data Model — Governanca de Tenants e RBAC Zero-Trust

## Overview

Modelo multi-tenant em PostgreSQL 15 com RLS (`CREATE POLICY`) e binding `SET LOCAL iabank.tenant_id`, managers/querysets tenant-first e campos PII protegidos por pgcrypto. Abrange lifecycle de tenants, versionamento de roles/políticas ABAC e trilhas auditáveis (WORM + `django-simple-history`), conforme spec `/specs/004-f-01-tenant-rbac-zero-trust/spec.md` e Arts. I, XI, XIII da constituição.

## Entities

### Tenant
- **Descrição**: Representa o espaço lógico isolado de um cliente/unidade. Fonte canônica para RLS e binding de sessão (`SET LOCAL`).  
- **Campos**:
  - `id` (UUID, PK) — referência para RLS.
  - `slug` (string, <= 64, único) — utilizado em domínios/subdomínios.
  - `display_name` (string, <= 128).
  - `allowed_domains` (string[], mínimo 1) — domínios autorizados para SSO.
  - `state` (enum: `pending`, `active`, `suspended`, `blocked`, `decommissioned`).
  - `risk_classification` (enum: `low`, `medium`, `high`) — define rate limiting inicial.
  - `region` (string, IANA TZ/ISO-3166) — usada em retenção/logs.
  - `retention_policy_days` (integer, >=365) — retenção aplicada em WORM; expurgo de sessão <=30 dias.
  - `idp_provider` (enum: `oidc`, `saml`).
  - `idp_metadata` (JSONB) — issuer, endpoints, certs, ACS/redirect; criptografado com pgcrypto.
  - `security_contacts` / `ops_contacts` (string[], email) — mín. 1 cada.
  - `hmac_salt_version` (string) — versão HKDF por tenant (rotacao 90d).
  - `etag` (string) — para controle otimista.
  - `created_at` / `updated_at` (timestamptz).  
- **Regras/RLS**:
  - Habilitar RLS e política: `tenant_id = current_setting('iabank.tenant_id')::uuid`.
  - `state` controla acesso: `suspended` read-only, `blocked` nega tudo, `decommissioned` só leitura de WORM.
  - `idp_metadata` criptografado; atributos mascarados em logs/traces.
  - Unicidade composta (`slug`, `allowed_domains[]`) por tenant, com índices tenant-first.

### TenantStateTransition
- **Descrição**: Histórico versionado das transições de estado do tenant (auditável/WORM).  
- **Campos**:
  - `id` (UUID, PK).
  - `tenant_id` (FK → Tenant.id).
  - `from_state` / `to_state` (enum conforme Tenant.state).
  - `reason` (text, requerido).
  - `actor_id` (UUID) — usuário autenticado (via IdP).
  - `trace_id` (string) — correlação OTEL/Sentry.
  - `created_at` (timestamptz).
  - `etag_snapshot` (string) — ETag antes/depois para auditoria.
- **Regras**:
  - Transições válidas: Pending→Active→Suspended→Blocked→Decommissioned; Blocked só retorna via revisão formal registrada.
  - Gera evento WORM com hash/assinatura verificados; fail-close se falhar upload.

### TenantSecurityProfile
- **Descrição**: Configurações de rate limiting, idempotência e chaves HMAC do tenant.  
- **Campos**:
  - `tenant_id` (PK, FK → Tenant.id).
  - `public_rps` (int) — default 50 (burst 100).
  - `private_rps` (int) — default 200 (burst 400).
  - `high_risk_multiplier` (decimal) — default 0.5 para tenants de alto risco.
  - `idempotency_ttl_hours` (int, default 24).
  - `hmac_key_version` (string) — ponteiro para chave ativa no Vault/KMS.
  - `rotates_at` (timestamptz) — próxima rotação planejada (<=90d).
  - `created_at` / `updated_at` (timestamptz).
- **Regras**:
  - Sempre referenciado em validação do middleware `X-Tenant-Id`/signature.
  - Rate limit aplicado por tenant e segmento (public/private) com Redis; alta criticidade aplica multiplicador.

### Role
- **Descrição**: Catálogo de roles por tenant, com versionamento e rollback seguro.  
- **Campos**:
  - `id` (UUID, PK).
  - `tenant_id` (FK → Tenant.id).
  - `slug` (string, <= 64, único por tenant).
  - `display_name` (string, <= 128).
  - `description` (text, opcional).
  - `current_version` (int, >=1).
  - `etag` (string) — para If-Match.
  - `created_at` / `updated_at` (timestamptz).
- **Regras**:
  - RLS: `tenant_id = current_setting('iabank.tenant_id')`.
  - Atualizações criam nova RoleVersion; `current_version` só avança, nunca reduz.

### RoleVersion
- **Descrição**: Snapshot versionado de permissões RBAC e políticas ABAC.  
- **Campos**:
  - `id` (UUID, PK).
  - `role_id` (FK → Role.id).
  - `version` (int, >=1).
  - `permissions` (string[], not null) — ações/escopos de recurso.
  - `abac_rules` (JSONB) — baseline de atributos obrigatórios (unidade, classificação, região, tipo de recurso) e custom aprovados; validado por JSON Schema 2020-12 `configs/abac/tenant-policy.schema.json`.
  - `policy_version` (string, SemVer) — versão declarada do schema aplicado.
  - `policy_checksum` (string, SHA-256) — hash do documento ABAC validado.
  - `status` (enum: `published`, `deprecated`).
  - `published_at` (timestamptz).
  - `created_by` (UUID) — usuário.
  - `checksum` (string, SHA-256) — integridade do payload.
  - `history_id` (FK → django-simple-history) — rastreio detalhado.
- **Regras**:
  - Nova versão exige `If-Match` da versão atual e gera histórico WORM.
  - Avaliação ABAC falha fechado (Problem Details 403/404) e registra evento mascarado.
  - Cache Redis `abac:{tenant_id}:{role_id}:{policy_version}` com TTL curto e verificação de `policy_checksum`; mismatch esvazia cache e recarrega do Postgres.

### RoleBinding
- **Descrição**: Associação normalizada de sujeito a role/versionamento.  
- **Campos**:
  - `id` (UUID, PK).
  - `tenant_id` (FK → Tenant.id).
  - `subject_id` (UUID) — usuário/sujeito do IdP.
  - `role_id` (FK → Role.id).
  - `role_version` (int) — versão aplicada ao binding.
  - `status` (enum: `active`, `revoked`).
  - `etag` (string).
  - `created_at` / `updated_at` (timestamptz).
- **Regras**:
  - RLS por `tenant_id`; `status=revoked` impede uso mesmo que Role esteja ativa.
  - Atualizações exigem `If-Match`; histórico auditável via WORM/histórico versionado.

### SubjectAttribute
- **Descrição**: Atributos do sujeito usados no ABAC baseline/custom.  
- **Campos**:
  - `id` (UUID, PK).
  - `tenant_id` (FK → Tenant.id).
  - `subject_id` (UUID).
  - `key` (string) — chaves permitidas pelo schema ABAC do tenant.
  - `values` (string[], minItems=1).
  - `claims_version` (string) — versão de claims do IdP usada na captura.
  - `created_at` / `updated_at` (timestamptz).
- **Regras**:
  - RLS por tenant; somente chaves/valores válidos pelo JSON Schema do tenant.
  - Atualização de atributos exige recálculo do cache ABAC e invalidação via `policy_checksum`.

### IdempotencyKeyRecord
- **Descrição**: Registro persistente de deduplicação para operações mutáveis.  
- **Campos**:
  - `id` (UUID, PK).
  - `tenant_id` (FK → Tenant.id).
  - `key` (string, unique).
  - `request_fingerprint` (string, hash do payload relevante).
  - `status` (enum: `pending`, `completed`, `failed`).
  - `response_code` (int) — última resposta associada.
  - `expires_at` (timestamptz, default now()+24h).
  - `created_at` (timestamptz).
- **Regras**:
  - Deduplicação primária em Redis (`idemp:{tenant}:{env}:{hash(key)}`) com TTL 24h; Postgres mantém trilha/auditoria sob RLS.
  - Reuso com fingerprint divergente retorna conflito (409/422).
  - RLS por `tenant_id`; usado por endpoints de tenant/role/auth.

### AuthorizationDecisionLog
- **Descrição**: Evento de decisão RBAC+ABAC com MFA e RLS, enviado para WORM/telemetria.  
- **Campos**:
  - `id` (UUID, PK).
  - `tenant_id` (FK → Tenant.id).
  - `user_id` (UUID).
  - `role_version` (int).
  - `attributes` (JSONB, mascarado) — baseline/custom avaliados.
  - `decision` (enum: `allow`, `deny`).
  - `reason` (string) — código/causa; nenhuma PII.
  - `trace_id` / `span_id` (string).
  - `created_at` (timestamptz).
- **Regras**:
  - Exportado para WORM com hash/assinatura; fail-close se integridade falhar.
  - Usado para dashboards por tenant e alerta de anomalias (reuse de refresh, 42x/429).

### RefreshToken
- **Descrição**: Token de refresh opaco, rotativo e auditável por tenant.  
- **Campos**:
  - `id` (UUID, PK).
  - `tenant_id` (FK → Tenant.id).
  - `user_id` (UUID, FK → User.id).
  - `session_id` (UUID) — agrupa cadeia de rotação.
  - `token_hash` (string) — HMAC-SHA256 do token opaco (chave por ambiente em Vault/KMS).
  - `status` (enum: `active`, `rotated`, `revoked`, `reused`).
  - `issued_at` / `expires_at` (timestamptz, default expiração 7 dias configurável).
  - `last_used_at` (timestamptz).
  - `replaced_by` (UUID FK → RefreshToken.id, opcional).
  - `fingerprint_hash` (string, opcional) — dispositivo/UA reduzido.
  - `ip_masked` (inet, opcional, mascarado).
  - `mfa_level` (enum: `totp`, `exception-code`).
- **Regras**:
  - RLS por `tenant_id`; refresh emitido sempre em cookie `HttpOnly; Secure; SameSite=Strict`.
  - Rotação a cada uso: novo registro `active`, anterior vira `rotated`/`replaced_by`; reuse de token rotado/revogado marca `reused`, revoga cadeia (`session_id`) e dispara alerta/telemetria.
  - Cache Redis opcional (TTL curto ~15 min) para `token_hash` → status; mismatch força leitura do Postgres.
  - Eventos de rotação/revogação/reuse são enviados ao WORM e spans/logs com `tenant_id`, `user_id`, `session_id`, `status` (sem PII).
