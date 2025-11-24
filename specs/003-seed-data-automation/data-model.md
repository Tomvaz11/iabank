# Data Model (Fase 1)

## Tenant
- **Tabela**: `tenancy_tenant` (já existente).  
- **Campos**: `id` (UUID PK), `slug` (unique), `environment` (`dev|staging|perf|dr|prod`), `rls_policy_version` (SemVer), `budget_caps` (JSONB), `off_peak_window_utc` (intervalo HH:MM-HH:MM).  
- **Índices/RLS**: índice composto iniciando por `id`; RLS obrigatória em todas as consultas; managers aplicam `tenant_id` por padrão.  
- **Uso**: FK obrigatório em todas as novas tabelas abaixo.

## SeedProfile (Manifesto)
- **Tabela**: `tenancy_seed_profile`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `profile` (texto), `schema_version` (ex.: `v1`), `version` (SemVer), `mode` (`baseline|carga|dr`), `reference_datetime` (timestamptz UTC), `volumetry` (JSONB caps Q11), `rate_limit` (JSONB limit/window), `backoff` (JSONB base/jitter/max_retries), `budget` (JSONB cost/error_budget), `window_start_utc`/`window_end_utc` (time), `ttl_days` (int), `slo_p95_ms`/`slo_p99_ms` (int), `integrity_hash` (texto), `salt_version` (texto).  
- **Constraints**: `unique(tenant_id, profile, version)`; check `window_start_utc != window_end_utc`; `reference_datetime` not null.  
- **Índices**: `index(tenant_id, profile)`, `index(tenant_id, mode)`, GIN em `volumetry` para consultas por entidade/cap.  
- **RLS**: policy `tenant_id = current_setting('app.tenant_id')::uuid`.
- **Forma dos JSONB**:  
  - `volumetry`: `<entity>` → `{cap: integer >=1, target_pct: number 0-100 opcional}`.  
  - `rate_limit`: `{limit: integer >=1, window_seconds: integer >=1, burst: integer opcional}`.  
  - `backoff`: `{base_seconds: integer >=1, jitter_factor: number 0-1, max_retries: integer >=0, max_interval_seconds: integer >= base_seconds}`.  
  - `budget`: `{cost_cap_brl: numeric(14,2) >=0, error_budget_pct: numeric(5,2) 0-100}`.  
  - **Validação**: JSON Schema 2020-12 publicado em `contracts/seed-profile.schema.json`; armazenar `integrity_hash` (sha256) do manifesto.

## SeedRun
- **Tabela**: `tenancy_seed_run`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_profile_id` (FK), `mode`, `status` (`queued|running|succeeded|failed|aborted|retry_scheduled|blocked`), `requested_by` (texto/RBAC subject), `idempotency_key` (texto), `trace_id`/`span_id` (texto), `rate_limit_usage` (JSONB: consumed/remaining), `error_budget_consumed` (numeric), `started_at`/`finished_at` (timestamptz), `reason` (JSONB Problem Details), `profile_version` (SemVer).  
- **Constraints**: `unique(tenant_id, seed_profile_id, idempotency_key)` com TTL (limpeza via job); status check; `idempotency_key` not null.  
- **Índices**: `index(tenant_id, status)`, `index(tenant_id, seed_profile_id)`, `index(tenant_id, started_at)`.  
- **RLS**: mesma política de tenant.
- **Forma dos JSONB**:  
  - `rate_limit_usage`: `{limit: int, remaining: int, reset_at: timestamptz}`.  
  - `reason`: Problem Details RFC 9457 completo (`type`, `title`, `status`, `detail`, `instance`, `violations[]`).  
  - `error_budget_consumed`: percentual (0-100) armazenado como numeric(5,2); aborta se >=100.

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
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_run_id` (FK uniq), `report_url` (URI WORM), `signature_hash` (texto), `worm_retention_days` (int ≥ 365), `integrity_status` (`pending|stored|verified|invalid`), `created_at` (timestamptz).  
- **Constraints**: `unique(seed_run_id)`, check retenção mínima; integridade obrigatória.  
- **RLS**: por tenant; WORM verificado antes de marcar `verified`.

## BudgetRateLimit
- **Tabela**: `tenancy_seed_budget_ratelimit`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_profile_id` (FK), `rate_limit_limit` (int), `rate_limit_window_seconds` (int), `budget_cost_cap` (numeric), `error_budget` (numeric), `rate_limit_remaining` (int), `reset_at` (timestamptz), `consumed_at` (timestamptz).  
- **Constraints**: valores não negativos; abort se `rate_limit_remaining` < 0 ou `error_budget` < 0.  
- **Índices**: `index(tenant_id, seed_profile_id)`, `index(tenant_id, reset_at)`.  
- **RLS**: por tenant; atualizado em cada lote/ack.
- **Forma dos JSONB/numéricos**: `budget_cost_cap` em BRL `numeric(14,2)`; `error_budget` percentual `numeric(5,2)` consumido conforme SLO/erros. Reset calculado por `rate_limit_window_seconds`; alertar em 80%, abortar em 100%.
