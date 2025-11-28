# Quickstart (Seeds, Factories e Manifests)

## Pre-requisitos
- RLS habilitado e politicas atualizadas para o tenant/ambiente alvo.  
- Acesso ao Vault Transit (paths segregados por ambiente/tenant) e variaveis de ambiente configuradas para client.  
- Manifesto YAML/JSON versionado em GitOps no padrao v1 (mode, volumetria/caps Q11, rate limit/backoff+jitter, budgets, TTL, off-peak UTC, reference_datetime ISO 8601, thresholds SLO/perf), validado pelo JSON Schema 2020-12.  
  Exemplos canônicos: `configs/seed_profiles/dev/tenant-a.yaml`, `configs/seed_profiles/homolog/tenant-a.yaml`, `configs/seed_profiles/staging/tenant-a.yaml` (baseline) e `configs/seed_profiles/perf/tenant-a.yaml` / `configs/seed_profiles/dr/tenant-a.yaml` (carga/DR).  
- WORM acessivel para persistir relatorios assinados; se indisponivel, nao executar.  
- Pipelines CI/PR com cobertura≥85%, ruff, SAST/DAST/SCA/SBOM e k6 habilitados.

### Manifesto baseline (exemplo resumido)
```yaml
metadata:
  tenant: tenant-a
  environment: staging
  profile: default
  version: 1.0.0
  schema_version: v1
  salt_version: v1
mode: baseline
reference_datetime: 2025-01-01T00:00:00Z
window:
  start_utc: "00:00"
  end_utc: "06:00"
volumetry:
  customers:
    cap: 100
  bank_accounts:
    cap: 120
rate_limit:
  limit: 120
  window_seconds: 60
backoff:
  base_seconds: 1
  jitter_factor: 0.1
  max_retries: 3
  max_interval_seconds: 60
ttl:
  baseline_days: 1
slo:
  p95_target_ms: 150
  p99_target_ms: 250
  throughput_target_rps: 1.5
integrity:
  manifest_hash: "<preenchido pelo pipeline>"
```

## Validar manifesto antes de rodar
```bash
curl -X POST https://api.iabank.local/api/v1/seed-profiles/validate \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-a" \
  -H "X-Environment: staging" \
  -H "Idempotency-Key: validate-$(uuidgen)" \
  -d "$(yq -o=json < configs/seed_profiles/staging/tenant-a.yaml)"
```
Resposta esperada: `200` com `valid=true` e `issues=[]`; falhas retornam Problem Details (`422`) com lista de campos/versoes incompatíveis ou `429` com `Retry-After` em caso de rate-limit/backoff. Cabeçalhos `RateLimit-*` e `Retry-After` sempre presentes; `Idempotency-Key` é obrigatório.
Idempotência: replays com a mesma `Idempotency-Key` (TTL 24h) retornam a mesma resposta (200/422/429); se o manifesto/hash divergir, retorna `409 idempotency_conflict`. Chaves são armazenadas no mesmo serviço de deduplicação usado pelo CLI/API de seed runs.

## Dry-run deterministico (CI/PR)
```bash
poetry run python backend/manage.py seed_data \
  --tenant-id <UUID_DO_TENANT> \
  --environment staging \
  --mode baseline \
  --manifest-path configs/seed_profiles/staging/tenant-a.yaml \
  --idempotency-key ci-$(uuidgen) \
  --dry-run
```
- Falha em `422` se manifesto/schema/tags divergem ou se o manifesto pertence a outro tenant; usa fallback de `Idempotency-Key` para `seed-data:<manifest_hash>` quando o parâmetro é omitido.  
- Locks: advisory lock por tenant/ambiente + fila curta com TTL=5 min; conflitos retornam código de saída `3` (cap global) ou `5` (fila pendente).  
- Determinismo: factories factory-boy e stubs Pact para integrações externas; nenhuma chamada real sai do container.  
- Reprova se PII não estiver mascarada, se payloads divergirem dos contratos `/api/v1` (Spectral/oasdiff), se caps Q11 do manifesto forem violados (fail-close) ou se `reference_datetime` divergir de checkpoints existentes (código `2` solicitando cleanup/reseed).

## Execucao em staging/perf (carga/DR)
```bash
poetry run python backend/manage.py seed_data \
  --tenant-id <UUID_DO_TENANT> \
  --environment perf \
  --mode dr \
  --manifest-path configs/seed_profiles/dr/tenant-a.yaml \
  --idempotency-key dr-$(uuidgen)
```
- Concorrecia serializada por tenant via advisory lock; fila curta Celery com acks tardios e DLQ configurados no serviço.  
- Aborta e registra Problem Details se 429 persistente ou budget/caps estourar; reagenda off-peak.

## Factories em testes
```python
from backend.apps.foundation.tests.factories import CustomerFactory

def test_factory_mascaramento(vault_stub):
    customer = CustomerFactory.build()
    assert customer.documento != "12345678901"  # PII mascarada
```
- Factories cobrem entidades core e validam contra serializers/contratos `/api/v1`.  
- Seeds de factory derivam de tenant/ambiente/manifesto para reproducao idempotente.

## Flags do CLI `seed_data`
- `--tenant-id <uuid>`: obrigatório; RLS/ABAC são avaliados com esse tenant.  
- `--environment <ambiente>`: obrigatório (`dev|homolog|staging|perf|dr`).  
- `--manifest-path <path>`: default `configs/seed_profiles/<env>/<tenant>.yaml`; se ausente, o comando monta um manifesto baseline mínimo para destravar a fila, mas o ideal é apontar para o manifesto versionado.  
- `--mode <baseline|carga|dr|canary>`: default = do manifesto ou `baseline` quando não informado.  
- `--dry-run`: roda sem checkpoints/WORM.  
- `--idempotency-key <str>`: opcional; fallback para `seed-data:<manifest_hash>`; conflito com manifesto divergente retorna código `2`.  
- `--role` (pode repetir) e `--requested-by`: usados pelo preflight; defaults via `SEED_ROLES` e `SEED_REQUESTED_BY`.  
- Códigos de saída: `0` sucesso; `2` validação/tenant mismatch/drift `reference_datetime`/idempotência; `3` lock/concorrência; `4` WORM/telemetria indisponível; `5` rate-limit/budget; `6` RLS/tenant ausente.

## Fluxo baseline + idempotência e locks
- Passo 1: validar o manifesto (`/seed-profiles/validate`), garantindo hash/integrity e tenant correto.  
- Passo 2: executar `seed_data` com `Idempotency-Key`; se omitido, o CLI usa o hash do manifesto e registra `manifest_hash` no stdout para auditoria.  
- Passo 3: o comando adquire lock advisory por tenant/ambiente, cria o `SeedRun/SeedBatch` e registra a entrada na fila com TTL 5 min; o id da fila aparece no stdout.  
- Drift de `reference_datetime`: se existir checkpoint para outro `reference_datetime`, o CLI encerra com código `2` e não cria entrada na fila; limpe checkpoints/datasets antes de reseedar.

## Stubs Pact/Prism (sem outbound real)
- Stubs obrigatórios para seeds: `contracts/pacts/financial-calculator.json`, `contracts/pacts/seed-data-outbound-block.json`, `contracts/pacts/kyc.json`, `contracts/pacts/pagamentos.json`, `contracts/pacts/notificacoes.json`.  
- Para servir localmente: `pnpm exec prism mock contracts/pacts/kyc.json --port 4010`, `--port 4011` para pagamentos e `--port 4012` para notificações (paths seguem os Pact).  
- CLI/API usam `SeedIntegrationService` e bloqueiam hosts fora da allowlist `localhost/127.0.0.1/prism/pact/stub`; configure `SEED_STUB_BASE` ou `SEED_KYC_URL/SEED_ANTIFRAUDE_URL/SEED_PAGAMENTOS_URL/SEED_NOTIFICACOES_URL` para apontar para os stubs.  
- O CI roda `scripts/ci/validate-seed-contracts.sh` e falha se os stubs não tiverem respostas 2xx + 429 para rate-limit/backoff; qualquer outbound real retorna Problem Details `external_calls_blocked` antes de enfileirar batches.

## Observabilidade e relatorios
- Traces/metricas/logs OTEL (W3C) com labels de tenant/ambiente/seed_run_id; PII sempre mascarada/redact.  
- Relatorio JSON assinado armazenado em WORM com `trace_id`, manifesto, volumetria, rate-limit usage, erros (Problem Details) e integridade verificada.  
- Falha em exportar OTEL/Sentry ou escrever WORM bloqueia conclusao e marca execucao como `failed`.
