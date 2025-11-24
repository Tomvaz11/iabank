# Data Model (Fase 1)

## Tenant
- Campos principais: `tenant_id` (UUID), `slug`, `ambiente`, `rls_policy_version`, `budget_caps`, `off_peak_window_utc`.  
- Relacoes: 1:N com `SeedProfile` e `SeedRun`; referencia politicas RLS versionadas.  
- Validacoes: `tenant_id` obrigatorio em toda query; bloqueio se RLS desativado ou `rls_policy_version` desatualizado.  
- Transicoes de estado: N/A (metadados estaveis; apenas versao de RLS pode ser promovida via GitOps).

## SeedProfile (Manifesto)
- Campos principais: `profile_id` (tenant+ambiente+nome), `schema_version`, `mode` (baseline|carga|dr), `reference_datetime` (ISO 8601 UTC), `volumetria_caps`, `rate_limit` (policy, limit, window), `backoff` (base, jitter, max_retries), `budget` (error_budget, cost_cap), `off_peak_window_utc`, `ttl`, `integrity_hash`, `version` (SemVer).  
- Relacoes: pertence a `Tenant`; referenciado por `SeedRun` e `Checkpoint`.  
- Validacoes: schema valido (v1), `reference_datetime` obrigatorio, caps/rate limit non-null, off-peak presente, `integrity_hash` consistente; versao incompatível falha fail-closed.  
- Transicoes: novas versoes promovidas via GitOps/Argo; mudanca de `reference_datetime` exige reseed/limpeza de checkpoints.

## SeedRun
- Campos principais: `seed_run_id` (UUID), `profile_id`, `mode`, `status` (queued|running|succeeded|failed|aborted|retry_scheduled|blocked), `requested_by` (subject/service-account), `idempotency_key`, `trace_id/span_id`, `rate_limit_usage`, `error_budget_consumed`, `started_at`, `finished_at`, `reason` (Problem Details).  
- Relacoes: 1:N com `SeedBatch` e `Checkpoint`; 1:1 com `EvidenceWORM`.  
- Validacoes: sempre referenciar `profile_id` ativo; `idempotency_key` unica com TTL; nao inicia se fora do off-peak ou sem RLS; aborta se orcamento/caps estourar.  
- Transicoes: queued -> running -> succeeded|failed|aborted; running -> retry_scheduled -> running; blocked (RLS/manifest) -> abort; cancel -> aborted.

## SeedBatch (Execucao Celery)
- Campos principais: `batch_id` (UUID), `seed_run_id`, `entity` (nome da entidade), `batch_size`, `attempt`, `dlq_attempts`, `status`, `last_retry_at`, `next_retry_at`.  
- Relacoes: pertence a `SeedRun`; gera `Checkpoint` e eventos OTEL.  
- Validacoes: `batch_size` respeita caps Q11 e rate limit; `attempt` controlado via DLQ/backoff; acks tardios habilitados; aborta se `dlq_attempts` exceder teto.  
- Transicoes: pending -> processing -> completed|failed|dlq; dlq -> retry_scheduled -> processing; fail-closed se exceder caps/429 persistente.

## Checkpoint
- Campos principais: `checkpoint_id` (UUID), `seed_run_id`, `entity`, `hash_estado`, `resume_token`, `percentual_concluido`, `created_at`.  
- Relacoes: 1:N por `SeedRun`/`SeedBatch`; usado para replays idempotentes.  
- Validacoes: `hash_estado` deve casar com manifest/version; `resume_token` criptografado/pgcrypto; invalida se manifest version divergir.  
- Transicoes: pending -> recorded -> sealed; sealed bloqueia reexecucao sem limpeza autorizada.

## DatasetSintetico
- Campos principais: `dataset_id`, `seed_run_id`, `entity`, `volumetria_prevista`, `volumetria_real`, `slo_target_p95`, `slo_target_p99`.  
- Relacoes: 1:N com `SeedRun`; consumido por testes/perf.  
- Validacoes: volumetria <= caps manifesto; p95/p99 medidos; drift entre previsto/real > tolerancia implica abort/rollback.  
- Transicoes: planned -> generated -> validated; validated -> published (apenas se WORM e contratos OK).

## FactoryTemplate
- Campos principais: `factory_name`, `entity`, `version`, `deterministic_seed` (derivado de tenant/ambiente/manifesto), `pii_fields`, `masking_strategy` (Vault Transit FPE), `supported_modes`.  
- Relacoes: compartilhado por testes e `SeedBatch`.  
- Validacoes: `pii_fields` catalogados; mascaramento obrigatorio; falha se depender de dados reais; compatibilidade com serializers `/api/v1`.  
- Transicoes: draft -> approved (pact/lint) -> deprecated; versao nova exige compat sem quebrar contrato.

## EvidenceWORM
- Campos principais: `evidence_id`, `seed_run_id`, `report_url`, `signature_hash`, `worm_retention`, `integrity_status`, `created_at`.  
- Relacoes: 1:1 com `SeedRun`; vinculo com commit/manifesto.  
- Validacoes: assinatura/hashes verificados; WORM acessivel; falha se integridade quebrar ou storage indisponivel.  
- Transicoes: pending -> stored -> verified; verified -> archived (respeitando retention).

## BudgetRateLimit
- Campos principais: `profile_id`, `rate_limit_limit`, `rate_limit_window`, `budget_cost_cap`, `error_budget`, `rate_limit_remaining`, `reset_at`.  
- Relacoes: agregado do manifesto consumido por `SeedRun`/`SeedBatch`.  
- Validacoes: nao pode iniciar execucao se `rate_limit_remaining` ou `error_budget` < 0; atualiza por retry/ack; 429 persistente aciona abort/reagendamento.  
- Transicoes: active -> exhausted (gatilha abort) -> reset (janela/manifesto novo).
