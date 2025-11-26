# Quickstart (Seeds, Factories e Manifests)

## Pre-requisitos
- RLS habilitado e politicas atualizadas para o tenant/ambiente alvo.  
- Acesso ao Vault Transit (paths segregados por ambiente/tenant) e variaveis de ambiente configuradas para client.  
- Manifesto YAML/JSON versionado em GitOps no padrao v1 (mode, volumetria/caps Q11, rate limit/backoff+jitter, budgets, TTL, off-peak UTC, reference_datetime ISO 8601, thresholds SLO/perf), validado pelo JSON Schema 2020-12.  
  Exemplos canônicos: `configs/seed_profiles/dev/tenant-a.yaml`, `configs/seed_profiles/homolog/tenant-a.yaml`, `configs/seed_profiles/staging/tenant-a.yaml` (baseline) e `configs/seed_profiles/perf/tenant-a.yaml` / `configs/seed_profiles/dr/tenant-a.yaml` (carga/DR).  
- WORM acessivel para persistir relatorios assinados; se indisponivel, nao executar.  
- Pipelines CI/PR com cobertura≥85%, ruff, SAST/DAST/SCA/SBOM e k6 habilitados.

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
  --profile configs/seed_profiles/staging/tenant-a.yaml \
  --mode baseline \
  --reference-datetime 2025-01-01T00:00:00Z \
  --dry-run \
  --idempotency-key ci-$(uuidgen)
```
- Fail-closed se manifesto versao/schema divergirem, se RLS ausente ou fora da janela off-peak.  
- Usa factories factory-boy deterministicas (seed derivado de tenant/ambiente/manifesto) e stubs Pact para integrações externas.  
- Reprova se PII não estiver mascarada, se payloads divergirem dos contratos `/api/v1` (Spectral/oasdiff) ou se caps Q11 do manifesto forem violados (fail-close).

## Execucao em staging/perf (carga/DR)
```bash
poetry run python backend/manage.py seed_data \
  --profile configs/seed_profiles/dr/tenant-a.yaml \
  --mode dr \
  --idempotency-key dr-$(uuidgen) \
  --concurrency 1 \
  --acks-late \
  --backoff jittered \
  --dlq
```
- Concorrecia serializada por tenant via advisory lock; fila curta Celery com acks tardios e DLQ.  
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
- `--profile <path>`: obrigatório. Caminho YAML/JSON GitOps do manifesto v1.  
- `--mode <baseline|carga|dr|canary>`: default = do manifesto; override opcional.  
- `--reference-datetime <ISO8601 UTC>`: default = do manifesto; override falha se divergente.  
- `--concurrency <int>`: default baseline=1; carga/DR/canary aceita 1–4 sob rate-limit/backoff do manifesto.  
- `--acks-late`: default `true`.  
- `--backoff <jittered|none>`: default `jittered` obedecendo manifesto (base/jitter/max_retries/max_interval).  
- `--dlq/--no-dlq`: default `--dlq`.  
- `--allow-offpeak-override`: default `false`; só permitido em dev isolado.  
- `--dry-run`: default `false`; roda em transação/snapshot e não grava checkpoints/WORM.  
- `--idempotency-key <str>`: obrigatório; falha se ausente.  
- Códigos de saída: `0` sucesso; `2` validação de manifesto/schema/contrato; `3` lock/concorrência; `4` WORM/telemetria indisponível; `5` rate-limit/budget; `6` RLS/tenant ausente.

## Observabilidade e relatorios
- Traces/metricas/logs OTEL (W3C) com labels de tenant/ambiente/seed_run_id; PII sempre mascarada/redact.  
- Relatorio JSON assinado armazenado em WORM com `trace_id`, manifesto, volumetria, rate-limit usage, erros (Problem Details) e integridade verificada.  
- Falha em exportar OTEL/Sentry ou escrever WORM bloqueia conclusao e marca execucao como `failed`.
