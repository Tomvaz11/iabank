# Data Model (Fase 1)

## Tenant
- **Tabela**: `tenancy_tenant` (já existente).  
- **Campos**: `id` (UUID PK), `slug` (unique), `environment` (`dev|homolog|staging|perf|dr|prod`), `rls_policy_version` (SemVer), `budget_caps` (JSONB), `off_peak_window_utc` (intervalo HH:MM-HH:MM), `maintenance_mode` (bool default false), `maintenance_note` (texto opcional), `maintenance_set_at` (timestamptz).  
- **Índices/RLS**: índice composto iniciando por `id`; RLS obrigatória em todas as consultas; managers aplicam `tenant_id` por padrão.  
- **Uso**: FK obrigatório em todas as novas tabelas abaixo.

## SeedProfile (Manifesto)
- **Tabela**: `tenancy_seed_profile`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `environment` (`dev|homolog|staging|perf|dr|prod`), `profile` (texto), `schema_version` (ex.: `v1`), `version` (SemVer), `mode` (`baseline|carga|dr|canary`), `reference_datetime` (timestamptz UTC), `volumetry` (JSONB caps Q11), `rate_limit` (JSONB limit/window/burst), `backoff` (JSONB base/jitter/max_retries/max_interval_seconds), `budget` (JSONB cost/error_budget), `window_start_utc`/`window_end_utc` (time, única janela off-peak, `end < start` indica cruzar meia-noite), `ttl_config` (JSONB `{baseline_days, carga_days, dr_days}`), `slo_p95_ms`/`slo_p99_ms` (int), `slo_throughput_rps` (numeric), `integrity_hash` (texto sha256), `salt_version` (texto), `canary_scope` (JSONB `{percentage|tenants[]}`), `manifest_path` (texto GitOps), `manifest_hash_sha256` (texto).  
- **Constraints**: `unique(tenant_id, profile, version)`, check `window_start_utc != window_end_utc`, `reference_datetime` not null, `mode != 'canary'` implica `canary_scope is null`, ttl por modo >= 0.  
- **Índices**: `index(tenant_id, profile)`, `index(tenant_id, mode)`, GIN em `volumetry`, GIN em `canary_scope`.  
- **RLS**: policy `tenant_id = current_setting('app.tenant_id')::uuid`.
- **Forma dos JSONB**:  
  - `volumetry`: `<entity>` → `{cap: integer >=1, target_pct: number 0-100 opcional}`.  
  - `rate_limit`: `{limit: integer >=1, window_seconds: integer >=1, burst: integer opcional}`.  
  - `backoff`: `{base_seconds: integer >=1, jitter_factor: number 0-1, max_retries: integer >=0, max_interval_seconds: integer >= base_seconds}`.  
  - `budget`: `{cost_cap_brl: numeric(14,2) >=0, error_budget_pct: numeric(5,2) 0-100}`.  
  - `ttl_config`: `{baseline_days: integer >=0, carga_days: integer >=0, dr_days: integer >=0}`.  
  - `canary_scope`: `{percentage: number 0-100} ou {tenants: array string unique, minItems=1}`.  
  - **Validação**: JSON Schema 2020-12 publicado em `contracts/seed-profile.schema.json`; armazenar `integrity_hash`/`manifest_hash_sha256` do manifesto.

## SeedRun
- **Tabela**: `tenancy_seed_run`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_profile_id` (FK), `environment` (`dev|homolog|staging|perf|dr|prod`), `mode`, `status` (`queued|running|succeeded|failed|aborted|retry_scheduled|blocked`), `requested_by` (texto/RBAC subject), `idempotency_key` (texto), `manifest_path` (texto), `manifest_hash_sha256` (texto), `reference_datetime` (timestamptz UTC), `trace_id`/`span_id` (texto), `rate_limit_usage` (JSONB: consumed/remaining/reset_at), `error_budget_consumed` (numeric), `started_at`/`finished_at` (timestamptz), `reason` (JSONB Problem Details), `profile_version` (SemVer), `dry_run` (bool), `offpeak_window` (tsrange opcional), `canary_scope_snapshot` (JSONB).  
- **Constraints**: `unique(tenant_id, seed_profile_id, idempotency_key)` com TTL (limpeza via job); status check; `idempotency_key` not null; `mode != 'canary'` implica `canary_scope_snapshot` null.  
- **Índices**: `index(tenant_id, status)`, `index(tenant_id, seed_profile_id)`, `index(tenant_id, started_at)`, `index(environment, status)`.  
- **RLS**: mesma política de tenant.
- **Forma dos JSONB**:  
  - `rate_limit_usage`: `{limit: int, remaining: int, reset_at: timestamptz}`.  
  - `reason`: Problem Details RFC 9457 completo (`type`, `title`, `status`, `detail`, `instance`, `violations[]`).  
  - `error_budget_consumed`: percentual (0-100) armazenado como numeric(5,2); aborta se >=100.  
  - `canary_scope_snapshot`: réplica do `canary_scope` do manifesto (percentage ou tenants) para auditoria.

## SeedBatch (Execução Celery)
- **Tabela**: `tenancy_seed_batch`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_run_id` (FK), `entity` (texto), `batch_size` (int), `attempt` (smallint), `dlq_attempts` (smallint), `status` (`pending|processing|completed|failed|dlq`), `last_retry_at`/`next_retry_at` (timestamptz), `caps_snapshot` (JSONB).  
- **Constraints**: check `batch_size > 0`; `attempt`/`dlq_attempts` >= 0; status enum.  
- **Índices**: `index(tenant_id, seed_run_id, entity)`, `index(tenant_id, status)`.  
- **RLS**: por tenant; `acks_late` exige idempotência no consumidor.
- **Forma dos JSONB**: `caps_snapshot` replica `volumetry[entity]` do manifesto para auditoria; validação impede cap < batch_size.

## Checkpoint
- **Tabela**: `tenancy_seed_checkpoint`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_run_id` (FK), `entity` (texto), `hash_estado` (texto), `resume_token` (bytea criptografado via pgcrypto), `percentual_concluido` (numeric 0–100), `created_at` (timestamptz), `sealed` (bool).  
- **Constraints**: check `percentual_concluido between 0 and 100`; `sealed` impede reuso sem limpeza.  
- **Índices**: `index(tenant_id, seed_run_id, entity)`, `index(tenant_id, created_at)`. TTL de limpeza até próximo reseed do modo (máx. 30 dias).  
- **RLS**: por tenant; validar hash/manifest version antes de retomar.

## SeedQueue (Controle de concorrência global)
- **Tabela**: `tenancy_seed_queue`.  
- **Campos**: `id` (UUID PK), `environment` (`dev|homolog|staging|perf|dr|prod`), `tenant_id` (FK opcional para filtrar serialização), `seed_run_id` (FK opcional), `status` (`pending|started|expired`), `enqueued_at` (timestamptz), `expires_at` (timestamptz), `lease_lock_key` (int8 derivado de advisory lock).  
- **Constraints**: TTL máximo 5 minutos (`expires_at > enqueued_at`), teto global de 2 execuções ativas por `environment`; expira acima do teto.  
- **Índices**: `index(environment, status, enqueued_at)`, `index(tenant_id, status)`.  
- **RLS**: por environment/tenant, alinhado às políticas de tenant; operações de lock usam advisory lock em conjunto com a fila.

## DatasetSintetico
- **Tabela**: `tenancy_seed_dataset`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_run_id` (FK), `entity`, `volumetria_prevista`/`volumetria_real` (int), `slo_target_p95`/`slo_target_p99` (int ms), `drift_percentual` (numeric).  
- **Constraints**: volumetria_real <= caps; drift > tolerância → marca run para abort.  
- **Índices**: `index(tenant_id, seed_run_id, entity)`.  
- **RLS**: por tenant; usado em gates de perf (k6).

## FactoryTemplate
- **Tabela**: `tenancy_factory_template`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK opcional se shareable), `factory_name`, `entity`, `version` (SemVer), `deterministic_seed` (texto), `pii_fields` (JSONB catálogo), `masking_strategy` (texto, ex.: `vault_transit_ff3-1`), `supported_modes` (array).  
- **Constraints**: `unique(factory_name, version, tenant_id nulls first)`; `pii_fields` não vazio para entidades com PII.  
- **Índices**: `index(factory_name, version)`.  
- **RLS**: se tenant-specific; factories globais só para dados não PII.
- **Forma dos JSONB**: `pii_fields` = array de `{field: string, format: string (cpf|cnpj|phone|email|address|free_text), mask: string (vault_transit_ff3-1|vault_transit_ff1)}`; `deterministic_seed` armazenado como sha256 hex derivado de `tenant+environment+manifest_version+salt_version`.

## EvidenceWORM
- **Tabela**: `tenancy_seed_evidence`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_run_id` (FK uniq), `report_url` (URI WORM), `signature_hash` (texto), `signature_algo` (texto, ex.: `RSA-PSS-SHA256` ou `Ed25519`), `key_id` (texto), `key_version` (texto), `worm_retention_days` (int ≥ 365), `integrity_status` (`pending|stored|verified|invalid`), `integrity_verified_at` (timestamptz opcional), `cost_model_version` (texto), `cost_estimated_brl` (numeric(14,2)), `cost_actual_brl` (numeric(14,2)), `created_at` (timestamptz).  
- **Constraints**: `unique(seed_run_id)`, check retenção mínima; integridade obrigatória; custos ≥ 0.  
- **RLS**: por tenant; WORM verificado antes de marcar `verified`.

## BudgetRateLimit
- **Tabela**: `tenancy_seed_budget_ratelimit`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_profile_id` (FK), `environment` (`dev|homolog|staging|perf|dr|prod`), `rate_limit_limit` (int), `rate_limit_window_seconds` (int), `budget_cost_cap` (numeric(14,2)), `budget_cost_estimated` (numeric(14,2)), `budget_cost_actual` (numeric(14,2)), `error_budget` (numeric(5,2)), `rate_limit_remaining` (int), `reset_at` (timestamptz), `consumed_at` (timestamptz), `throughput_target_rps` (numeric), `budget_alert_at_pct` (numeric default 80.00), `cost_model_version` (texto), `cost_window_started_at` (timestamptz), `cost_window_ends_at` (timestamptz).  
- **Constraints**: valores não negativos; alertar em `budget_alert_at_pct`, abort se `rate_limit_remaining` < 0 ou `error_budget` >= 100; `budget_cost_actual`/`budget_cost_estimated` >= 0.  
- **Índices**: `index(tenant_id, seed_profile_id)`, `index(tenant_id, reset_at)`, `index(environment, reset_at)`, `index(environment, cost_window_ends_at)`.  
- **RLS**: por tenant; atualizado em cada lote/ack.
- **Forma dos JSONB/numéricos**: `budget_cost_cap` em BRL `numeric(14,2)`; `error_budget` percentual `numeric(5,2)` consumido conforme SLO/erros; `throughput_target_rps` alinhado ao manifesto. Reset calculado por `rate_limit_window_seconds`; alertar em 80%, abortar em 100%; janela de custo definida por `cost_window_started_at`/`cost_window_ends_at`.

## SeedIdempotency
- **Tabela**: `tenancy_seed_idempotency`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `environment` (`dev|homolog|staging|perf|dr|prod`), `idempotency_key` (texto), `manifest_hash_sha256` (texto), `mode` (`baseline|carga|dr|canary`), `seed_run_id` (FK opcional para reutilização), `expires_at` (timestamptz), `created_at` (timestamptz default now).  
- **Constraints**: `unique(tenant_id, environment, idempotency_key)` com TTL (GC 24h via Argo Cron); `expires_at > created_at`; se `seed_run_id` presente, `manifest_hash_sha256` deve casar com o run.  
- **Índices**: `index(tenant_id, environment, expires_at)`, `index(manifest_hash_sha256)` para reuso rápido.  
- **RLS**: por tenant; bloqueia acesso cruzado e evita dedupe entre tenants.  
- **Uso**: deduplicação de CLI/API compartilhada; conflito de chave com manifesto divergente → Problem Details `idempotency_conflict` (`409`); igual → retorna run existente.

## SeedRBAC
- **Tabela**: `tenancy_seed_rbac`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `environment` (`dev|homolog|staging|perf|dr|prod`), `subject` (texto; service account ou user id), `role` enum (`seed-runner`, `seed-admin`, `seed-read`), `policy_version` (SemVer), `created_at` (timestamptz).  
- **Constraints**: `unique(tenant_id, environment, subject)`; role enum fechada; `policy_version` obrigatório.  
- **Índices**: `index(tenant_id, environment, role)`, `index(tenant_id, subject)`.  
- **RLS**: por tenant; leitura/escrita restrita ao admin de tenant.  
- **Uso**: permission class DRF `SeedDataPermission` e CLI consultam esta tabela para RBAC/ABAC (bindings por tenant/ambiente), vinculando `policy_version` ao span OTEL/auditoria.

## Banking Domain (entidades seedadas)

### TenantUser (service accounts para seeds)
- **Tabela**: `tenancy_user` (ou `auth_user` custom com FK `tenant_id`).  
- **Campos**: `id` (PK int ou UUID conforme base), `tenant_id` (FK), `username` (unique por tenant), `email` (unique por tenant), `password` (hash), flags de staff/superuser (`false` por padrão).  
- **Constraints**: `unique(tenant_id, username)`, `unique(tenant_id, email)`; service accounts criadas para `seed-runner/admin/read`.  
- **RLS**: `tenant_id = current_setting('app.tenant_id')::uuid`.  
- **Uso**: satisfazer `tenant_users` no manifesto; provisionar apenas contas técnicas com roles do RBAC.

### Customer
- **Tabela**: `banking_customer`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `name` (varchar 255), `document_number` (char 20, pgcrypto+FPE), `birth_date` (date null), `email` (EmailField null), `phone` (char 20 null), `status` enum (`ACTIVE|BLOCKED|DELINQUENT|CANCELED`), `created_at/updated_at`.  
- **Constraints**: `unique(tenant_id, document_number)`, status default `ACTIVE`.  
- **Índices**: `index(tenant_id, status)`.  
- **RLS**: por tenant, managers aplicam `tenant_id`.  
- **PII**: `document_number`, `email`, `phone` cifrados com pgcrypto + mascaramento FPE.

### Address
- **Tabela**: `banking_address`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `customer_id` (FK), `zip_code` (char 10), `street` (varchar 255), `number` (varchar 20), `complement` (varchar 100 opcional), `neighborhood` (varchar 100), `city` (varchar 100), `state` (char 2), `is_primary` (bool default false).  
- **Constraints**: `CHECK (state ~ '^[A-Z]{2}$')`; opcional `unique(customer_id) WHERE is_primary`.  
- **Índices**: `index(customer_id, is_primary)`.  
- **RLS**: por tenant via FK + policy.

### Consultant
- **Tabela**: `banking_consultant`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `user_id` (FK → `tenancy_user`), `balance` (decimal(10,2) default 0.00), `created_at/updated_at`.  
- **Constraints**: `unique(user_id)`; saldo não negativo (`balance >= 0`).  
- **RLS**: por tenant.

### BankAccount
- **Tabela**: `banking_bank_account`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `customer_id` (FK PROTECT), `name` (varchar 100), `agency` (char 10, FPE), `account_number` (char 20, FPE), `initial_balance` (decimal(15,2) default 0.00), `type` enum (`CHECKING|SAVINGS`), `status` enum (`ACTIVE|BLOCKED`), `created_at/updated_at`.  
- **Constraints**: `unique(tenant_id, account_number)`, `unique(tenant_id, agency, account_number)`; status default `ACTIVE`.  
- **Índices**: `index(tenant_id, status)`, `index(customer_id)`.  
- **RLS/PII**: por tenant; `agency/account_number` com pgcrypto+FPE.

### AccountCategory
- **Tabela**: `banking_account_category`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `code` (varchar 40), `description` (varchar 255), `is_default` (bool default false).  
- **Constraints**: `unique(tenant_id, code)`; apenas um `is_default=true` por tenant (check parcial).  
- **Índices**: `index(tenant_id, is_default)`.  
- **RLS**: por tenant.

### Supplier
- **Tabela**: `banking_supplier`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `name` (varchar 255), `document_number` (char 20, FPE, null permitido), `status` enum (`ACTIVE|BLOCKED`), `created_at/updated_at`.  
- **Constraints**: `unique(tenant_id, document_number)` quando não nulo; status default `ACTIVE`.  
- **RLS/PII**: por tenant; `document_number` com pgcrypto+FPE.

### Loan
- **Tabela**: `banking_loan`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `customer_id` (FK PROTECT), `consultant_id` (FK PROTECT), `principal_amount` (decimal(12,2)), `interest_rate` (decimal(5,2)), `number_of_installments` (smallint), `contract_date` (date), `first_installment_date` (date), `status` enum (`IN_PROGRESS|PAID_OFF|IN_COLLECTION|CANCELED`), `iof_amount` (decimal(10,2)), `cet_annual_rate` (decimal(7,4)), `cet_monthly_rate` (decimal(7,4)), `created_at/updated_at`.  
- **Constraints**: `number_of_installments > 0`; status default `IN_PROGRESS`.  
- **Índices**: `index(tenant_id, status)`, `index(customer_id)`, `index(consultant_id)`.  
- **RLS**: por tenant.

### Installment
- **Tabela**: `banking_installment`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `loan_id` (FK CASCADE), `installment_number` (smallint), `due_date` (date), `amount_due` (decimal(10,2)), `amount_paid` (decimal(10,2) default 0.00), `payment_date` (date null), `status` enum (`PENDING|PAID|OVERDUE|PARTIALLY_PAID`), `created_at/updated_at`.  
- **Constraints**: `unique(loan_id, installment_number)`; `amount_due >= 0`; status default `PENDING`.  
- **Índices**: `index(tenant_id, status)`, `index(loan_id, due_date)`.  
- **RLS**: por tenant.

### FinancialTransaction
- **Tabela**: `banking_financial_transaction`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `description` (varchar 255), `amount` (decimal(12,2)), `transaction_date` (date), `is_paid` (bool default false), `payment_date` (date null), `type` enum (`INCOME|EXPENSE`), FKs opcionais `bank_account_id` (PROTECT), `category_id` (SET NULL), `cost_center_id` (SET NULL), `supplier_id` (SET NULL), `installment_id` (SET NULL), `created_at/updated_at`.  
- **Constraints**: `amount >= 0`; `payment_date` não nulo quando `is_paid=true` (check).  
- **Índices**: `index(tenant_id, type)`, `index(bank_account_id)`.  
- **RLS/PII**: por tenant; campos de referência mascarados onde aplicável.

### CreditLimit
- **Tabela**: `banking_credit_limit`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `bank_account_id` (FK), `current_limit` (decimal(12,2)), `used_amount` (decimal(12,2) default 0.00), `status` enum (`ACTIVE|FROZEN|CANCELED`), `effective_from`/`effective_through` (date null).  
- **Constraints**: `current_limit >= 0`, `used_amount >= 0`, `unique(tenant_id, bank_account_id)`; status default `ACTIVE`.  
- **Índices**: `index(tenant_id, status)`, `index(bank_account_id)`.  
- **RLS**: por tenant.

### Contract
- **Tabela**: `banking_contract`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `bank_account_id` (FK opcional), `customer_id` (FK opcional), `body` (JSONB), `etag_payload` (char 64 sha256), `version` (SemVer), `status` enum (`ACTIVE|REVOKED|EXPIRED`), `signed_at` (timestamptz), `pii_redacted` (bool default true), `created_at/updated_at`.  
- **Constraints**: `unique(tenant_id, etag_payload)`; `body` não nulo; status default `ACTIVE`.  
- **Índices**: `index(tenant_id, status)`.  
- **RLS/PII**: por tenant; PII já mascarada antes de persistir/assinar.
