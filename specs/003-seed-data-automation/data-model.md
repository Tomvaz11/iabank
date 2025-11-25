# Data Model (Fase 1)

## Tenant
- **Tabela**: `tenancy_tenant` (já existente).  
- **Campos**: `id` (UUID PK), `slug` (unique), `environment` (`dev|staging|perf|dr|prod`), `rls_policy_version` (SemVer), `budget_caps` (JSONB), `off_peak_window_utc` (intervalo HH:MM-HH:MM), `maintenance_mode` (bool default false), `maintenance_note` (texto opcional), `maintenance_set_at` (timestamptz).  
- **Índices/RLS**: índice composto iniciando por `id`; RLS obrigatória em todas as consultas; managers aplicam `tenant_id` por padrão.  
- **Uso**: FK obrigatório em todas as novas tabelas abaixo.

## SeedProfile (Manifesto)
- **Tabela**: `tenancy_seed_profile`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `environment` (`dev|staging|perf|dr|prod`), `profile` (texto), `schema_version` (ex.: `v1`), `version` (SemVer), `mode` (`baseline|carga|dr|canary`), `reference_datetime` (timestamptz UTC), `volumetry` (JSONB caps Q11), `rate_limit` (JSONB limit/window/burst), `backoff` (JSONB base/jitter/max_retries/max_interval_seconds), `budget` (JSONB cost/error_budget), `window_start_utc`/`window_end_utc` (time, única janela off-peak, `end < start` indica cruzar meia-noite), `ttl_config` (JSONB `{baseline_days, carga_days, dr_days}`), `slo_p95_ms`/`slo_p99_ms` (int), `slo_throughput_rps` (numeric), `integrity_hash` (texto sha256), `salt_version` (texto), `canary_scope` (JSONB `{percentage|tenants[]}`), `manifest_path` (texto GitOps), `manifest_hash_sha256` (texto).  
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
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_profile_id` (FK), `environment` (`dev|staging|perf|dr|prod`), `mode`, `status` (`queued|running|succeeded|failed|aborted|retry_scheduled|blocked`), `requested_by` (texto/RBAC subject), `idempotency_key` (texto), `manifest_path` (texto), `manifest_hash_sha256` (texto), `reference_datetime` (timestamptz UTC), `trace_id`/`span_id` (texto), `rate_limit_usage` (JSONB: consumed/remaining/reset_at), `error_budget_consumed` (numeric), `started_at`/`finished_at` (timestamptz), `reason` (JSONB Problem Details), `profile_version` (SemVer), `dry_run` (bool), `offpeak_window` (tsrange opcional), `canary_scope_snapshot` (JSONB).  
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
- **Campos**: `id` (UUID PK), `environment` (`dev|staging|perf|dr|prod`), `tenant_id` (FK opcional para filtrar serialização), `seed_run_id` (FK opcional), `status` (`pending|started|expired`), `enqueued_at` (timestamptz), `expires_at` (timestamptz), `lease_lock_key` (int8 derivado de advisory lock).  
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
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_run_id` (FK uniq), `report_url` (URI WORM), `signature_hash` (texto), `worm_retention_days` (int ≥ 365), `integrity_status` (`pending|stored|verified|invalid`), `created_at` (timestamptz).  
- **Constraints**: `unique(seed_run_id)`, check retenção mínima; integridade obrigatória.  
- **RLS**: por tenant; WORM verificado antes de marcar `verified`.

## BudgetRateLimit
- **Tabela**: `tenancy_seed_budget_ratelimit`.  
- **Campos**: `id` (UUID PK), `tenant_id` (FK), `seed_profile_id` (FK), `environment` (`dev|staging|perf|dr|prod`), `rate_limit_limit` (int), `rate_limit_window_seconds` (int), `budget_cost_cap` (numeric(14,2)), `error_budget` (numeric(5,2)), `rate_limit_remaining` (int), `reset_at` (timestamptz), `consumed_at` (timestamptz), `throughput_target_rps` (numeric), `budget_alert_at_pct` (numeric default 80.00).  
- **Constraints**: valores não negativos; alertar em `budget_alert_at_pct`, abort se `rate_limit_remaining` < 0 ou `error_budget` >= 100.  
- **Índices**: `index(tenant_id, seed_profile_id)`, `index(tenant_id, reset_at)`, `index(environment, reset_at)`.  
- **RLS**: por tenant; atualizado em cada lote/ack.
- **Forma dos JSONB/numéricos**: `budget_cost_cap` em BRL `numeric(14,2)`; `error_budget` percentual `numeric(5,2)` consumido conforme SLO/erros; `throughput_target_rps` alinhado ao manifesto. Reset calculado por `rate_limit_window_seconds`; alertar em 80%, abortar em 100%.
