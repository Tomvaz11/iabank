# Implementation Plan: Automacao de seeds, dados de teste e factories

**Branch**: `003-seed-data-automation` | **Date**: 2025-11-24 | **Spec**: `/home/pizzaplanet/meus_projetos/iabank/specs/003-seed-data-automation/spec.md`
**Input**: Feature specification from `/home/pizzaplanet/meus_projetos/iabank/specs/003-seed-data-automation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementar automacao de seeds/factories deterministicas e 100% sinteticas para baseline, carga e DR multi-tenant, governadas por manifestos versionados e contratos `/api/v1` (spec.md, clarifications-archive.md, ADR-008/010/011/012 citados no spec). A solucao usa monolito Django/DRF sobre PostgreSQL com RLS/pgcrypto, Celery/Redis para execucoes idempotentes com backoff/jitter, acks tardios e DLQ (Blueprint §26) e evidencia WORM assinada (Art. I, XI, XIII, XVI). Fluxo segue Test-First (Art. III), release seguro com flags/canary e GitOps/Argo CD (Art. VIII, XVIII), bloqueando execucao fora de off-peak, rate limit/budget ou sem mascaramento PII via Vault Transit.

## Technical Context

Preencha cada item com o plano concreto para a feature. Use `[NEEDS CLARIFICATION]` quando houver incerteza e registre no `/clarify`. Referencie os artigos da constituição e ADRs que sustentam cada decisão.

**Language/Version**: Python 3.11 para backend/CLI; Node.js 20 para lint/diff/contratos (Art. I)  
**Primary Dependencies**: Django 4.2 LTS, DRF 3.15, Celery 5.3, Redis 7, factory-boy, OpenAPI tooling (Spectral/Prism/Pact), k6, Vault Transit client, OpenTelemetry SDK, Sentry (Blueprint §§3.1/6/26; ADR-008/010/011/012)  
**Storage**: PostgreSQL 15 com pgcrypto/RLS obrigatorios; WORM storage para relatorios assinados; Redis como broker/estado de fila curta; Vault Transit para FPE deterministica  
**Testing**: pytest + pytest-django/DRF client, factory-boy, contract tests (OpenAPI lint/diff + Pact stubs), k6 perf gate, check-docs-needed, ruff/coverage≥85% (Art. III, IV, IX, XI)  
**Target Platform**: Linux/Kubernetes para runtime e CI/CD (Argo CD/GitOps), compatibilidade local via Docker/venv; pipelines CI PR  
**Project Type**: Monolito web/backend com tarefas Celery e CLI de management commands  
**Performance Goals**: Cumprir SLO/SLI por manifesto (p95/p99 de execucao seed_data), RPO≤5 min e RTO≤60 min para DR, respeitando rate limit/budgets e throughput controlado  
**Constraints**: Execucao apenas com RLS ativo e RBAC/ABAC minimo, off-peak window em UTC, caps de volumetria (Q11) e rate limit por tenant/ambiente, dados sinteticos sem snapshots de producao, expand/contract para evolucao de schema  
**Scale/Scope**: Multi-tenant, modos baseline/carga/DR, concorrencia serializada por tenant/ambiente com fila curta e teto global por ambiente/cluster; contratos `/api/v1` governados por lint/diff/contrato

### Contexto Expandido

**Backend**: Monolito Django/DRF (Art. I) com management command `seed_data` orquestrando manifestos e chamando services Celery para lotes idempotentes; uso de `backend/apps/tenancy` (locks/RLS) e `backend/apps/foundation` (idempotency, metrics) com padrao layered e managers forçando tenant_id.  
**Frontend**: N/A para entrega inicial; apenas contratos REST `/api/v1` versionados e validados, preservando FSD existente (Art. I).  
**Async/Infra**: Celery 5.3 + Redis 7 (broker/fila curta) com acks tardios, backoff/jitter e DLQ (Blueprint §26); locks via advisory lock Postgres; pipelines Argo CD/GitOps; Terraform+OPA para Vault/WORM/filas (Art. XIV).  
**Persistência/Dados**: PostgreSQL 15 com RLS ativo, pgcrypto; politicas `CREATE POLICY` versionadas; schemas evoluem por expand/contract com `CONCURRENTLY`; PII cifrada via Vault Transit; WORM para relatorios assinados.  
**Testing Detalhado**: TDD com pytest/pytest-django, factories factory-boy deterministicas por tenant/ambiente/manifesto, testes de integracao `/api/v1` com RateLimit/Idempotency-Key/ETag e Problem Details, contract tests (OpenAPI lint/diff + Pact stubs), k6 para gate de perf, dry-run deterministico no CI (Art. III, IV, IX, XI).  
**Observabilidade**: OTEL com W3C Trace Context, structlog/django-prometheus/Sentry (ADR-012); traces/metricas/logs etiquetados por tenant/ambiente/execucao; redacao de PII obrigatoria; export falho bloqueia. SLOs/SLIs (p95/p99/throughput/error budget) vivem em `docs/slo/seed-data.md` e alimentam k6 e o relatório WORM.  
**Segurança/Compliance**: RBAC/ABAC minimo para `seed_data`, RLS enforced, mascaramento PII deterministico (Vault Transit FPE), FinOps budgets/caps por manifesto, evidencias WORM assinadas, mocks para integrações externas (OWASP/NIST; Art. XII, XIII, XVI).  
**Performance Targets**: p95/p99 de execucao por manifesto (fonte = manifesto por ambiente/tenant) dentro do budget; throughput alinhado a RateLimit-* e idempotencia; DR cumpre RPO≤5 min/RTO≤60 min; error budget consumido/abortado conforme manifesto.  
**Restrições Operacionais**: TDD/integ-primeiro, execucao apenas em janela off-peak declarada, bloqueio sem RLS ou drift de manifesto, RLS check preflight, somente dados sinteticos (proibido snapshot/dump de producao), GitOps/Argo CD com flags/canary/rollback e deteccao de drift/off-peak; expand/contract para schema; pipeline/Argo falha se não cumprir Trunk-Based (branches curtas, histórico linear, squash-only) ou rollback ensaiado (Art. VIII, adicoes_blueprint §1). Canary é opcional (apenas se modo canary for adotado).
**Escopo/Impacto**: Tenants/ambientes multi-tenant, modos baseline/carga/DR, APIs `/api/v1` consumidas/testadas, pipelines CI/CD, infra de Vault/WORM/filas/Terraform; sem dependencias externas reais (stubs Pact).

## Constitution Check

*GATE: Validar antes da Fase 0 e reconfirmar apos o desenho de Fase 1.*

- [x] **Art. III - TDD**: Suites pytest/pytest-django planejadas para `seed_data` (baseline/carga/DR), factories com mascaramento e checagens de idempotencia/rate-limit; iniciar em `/home/pizzaplanet/meus_projetos/iabank/backend/apps/**/tests/` com falha antes de codigo.  
- [x] **Art. VIII - Lancamento Seguro**: Flags/canary por ambiente/tenant, rollback via Argo CD, budget de erro por manifesto e relatorio WORM vinculado; documentado neste plano e quickstart.  
- [x] **Art. IX - Pipeline CI**: Cobertura≥85%, complexidade≤10, SAST/DAST/SCA/SBOM, k6 perf gate e dry-run deterministico mapeados; falha bloqueia promocao (ver spec/quickstart).  
- [x] **Art. XI - Governanca de API**: Contratos OpenAPI 3.1 em `contracts/seed-data.openapi.yaml` e alinhamento a `contracts/api.yaml`; lint/diff/Pact previstos e versionamento SemVer.  
- [x] **Art. XIII - Multi-tenant & LGPD**: RLS obrigatório com managers aplicando tenant_id, testes anti-cross-tenant, mascaramento Vault Transit FPE e PII cifrada; fail-closed sem RLS.  
- [x] **Art. XVIII - Fluxo Spec-Driven**: Artefatos atualizados (`spec.md`, `clarifications-archive.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`); `tasks.md` sera gerado na proxima fase via `/speckit.tasks`.

## Project Structure

### Documentacao (esta feature)

Arquivos em `/home/pizzaplanet/meus_projetos/iabank/specs/003-seed-data-automation/` alinhados ao fluxo `/constitution -> /specify -> /clarify -> /plan -> /tasks`:

```
specs/003-seed-data-automation/
|-- spec.md                # aprovado em /specify
|-- clarifications-archive.md
|-- plan.md                # este plano
|-- research.md            # Fase 0 (respostas a NEEDS CLARIFICATION e decisoes)
|-- data-model.md          # Fase 1 (entidades e validacoes)
|-- quickstart.md          # Fase 1 (como usar seed_data/factories)
`-- contracts/             # Fase 1 (OpenAPI 3.1 e stubs Pact gerados)
```

### Codigo-Fonte (repositorio)

Diretorios a serem alterados/estendidos respeitando monolito modular (Art. I/II):

```
backend/apps/tenancy/management/commands/    # novo comando seed_data serializando por tenant/ambiente com advisory lock
backend/apps/tenancy/tests/                  # TDD e validacoes RLS/locks/idempotencia
backend/apps/foundation/{services,models}    # servicos de idempotencia/checkpoints, metrics, mascaramento PII integrado ao Vault
backend/apps/contracts/                      # contratos OpenAPI 3.1 e pact stubs para /api/v1 usados nas seeds/factories
backend/apps/foundation/tests/               # factories factory-boy e checagens de PII/rate-limit/idempotency-key
contracts/                                   # artefatos OpenAPI 3.1 (lint/diff) e pact files contratuais
infra/                                       # Terraform/OPA para Vault/WORM/filas e pipelines Argo CD (GitOps)
observabilidade/                             # configuracao OTEL/Sentry/logs rotulados por tenant/execucao
docs/                                        # runbooks, checklists PII/RLS, relatorio WORM/DR
```

**Structure Decision**: Reutiliza apps existentes (`tenancy` para isolamento/locks/RLS, `foundation` para idempotencia/observabilidade) evitando novo modulo desnecessario. Contratos ficam em `contracts/` conforme Art. XI. Infra permanece em `infra/` com Terraform/OPA (Art. XIV). Esta distribuicao preserva separacao de responsabilidades em camadas e facilita testes/observabilidade centralizados.

### Endpoint de validacao de manifestos

- **Contrato**: `/api/v1/seed-profiles/validate` ja descrito em `contracts/seed-data.openapi.yaml` (OpenAPI 3.1, Problem Details, RateLimit-*, Idempotency-Key).  
- **Handler**: `backend/apps/tenancy/views.py:SeedProfileValidateView` registrado em `backend/apps/tenancy/urls.py` sob `path("api/v1/seed-profiles/validate", ...)`, respeitando middleware de RLS/tenant e ABAC.  
- **Regras**: Valida schema v1 do manifesto (JSON Schema 2020-12) incluindo `mode` (baseline/carga/dr), `reference_datetime` ISO 8601 UTC, janela off-peak `start_utc/end_utc` (única, pode cruzar meia-noite), caps Q11 por entidade, rate limit/backoff+jitter, budget/TTL e `salt_version`. Falha fail-closed em: versão incompatível, drift de campos obrigatórios, janela fora do formato ou caps ausentes.  
- **Respostas**: `200` com `valid=true`, `issues=[]`, `normalized_version` e `caps` extraídos; `422` Problem Details com lista de issues; `429` aplica backoff curto; `401/403` em ausência de autorização/RLS. Sempre retorna `RateLimit-*`, `Retry-After` e exige `Idempotency-Key`.  
- **Observabilidade**: OTEL + Sentry com labels `tenant_id`, `environment`, `manifest_version`, `reference_datetime`, marcando chamadas inválidas como `error` e emitindo métricas de taxa de rejeição (Art. VII/ADR-012).  
- **Stubs/Tests**: Stubs Pact/Prism gerados do contrato; teste de integração em `backend/apps/tenancy/tests/test_seed_profile_validate_api.py` cobre happy path e 422, incluindo headers obrigatórios e Problem Details.

### Fluxo operacional do comando `seed_data`

- **Preflight**: Checar migrations pendentes; validar enforcement de RLS (Art. XIII), flags/canary do domínio e disponibilidade do Vault/WORM (bucket, role/KMS, retenção, chave FPE ativa no Vault); reforçar RBAC/ABAC mínimo para acesso a chaves/manifestos e registrar auditoria com redaction; abortar fail-closed se qualquer pré-condição falhar, retornando Problem Details e sem enfileirar lotes.  
- **Validação de manifesto**: Carregar manifesto YAML/JSON (GitOps) e validar contra JSON Schema v1 (JSON Schema 2020-12). Campos obrigatórios: `metadata` (tenant, ambiente, profile/version, salt_version), `mode` (baseline/carga/dr), `reference_datetime` ISO 8601 UTC, `window.start_utc/end_utc` (única, pode cruzar meia-noite), `volumetry` por entidade (caps Q11), `rate_limit` (limit/window) + `backoff` (base/jitter/max_retries), `budget` (cost/error budget), `ttl` por modo, `slo` (p95/p99 alvo), `caps_override` opcional para dev. Versão divergente ou ausência de campos → fail-closed.  
- **Concorrência/locks**: Adquirir lock global (teto 2 execuções por ambiente/cluster, TTL fila 5 min) e lock por tenant/ambiente via advisory lock (TTL 60s) no Postgres; fila curta auditável no DB; liberação em finally; se lock expirar, reagendar.  
- **Criação de SeedRun/SeedBatch**: Persistir `SeedRun` com `idempotency_key`, status `queued` e manifesto referenciado; para cada entidade/caps gerar `SeedBatch` inicial com attempt=0 e status `pending`.  
- **Execução (Celery/Redis)**: Disparar lotes Celery com `acks_late`, backoff com jitter em 429/erro transitório, DLQ com teto de tentativas definido no manifesto; baseline sequencial, carga/DR com paralelismo controlado (2–4 workers) respeitando rate limit centralizado.  
- **Formação/ordenação de batches**: Ordenar entidades respeitando FKs/dependências: `tenant_users -> customers -> addresses -> bank_accounts -> account_categories -> suppliers -> loans -> installments -> financial_transactions -> limits -> contracts`. `batch_size` determinístico: `baseline` usa `min(cap, 200)`, `carga/dr` usa `min(cap, 1000)` limitado por rate limit; dividir usando `factory_seed` para ordenação (sha256 do tenant+environment+manifest_version+salt_version) garantindo reprodutibilidade. Batches que excederem cap ou quebrarem ordem de dependência falham em fail-closed.  
- **Checkpoints/idempotência**: Cada lote grava `Checkpoint` (hash_estado, resume_token criptografado via pgcrypto) e atualiza `SeedRun`/`BudgetRateLimit`; divergência de hash ou checkpoint vencido → abort e exigir limpeza/reseed. Mudança de `reference_datetime` no manifesto é tratada como drift: o run falha antes de executar e força limpeza coordenada de checkpoints antes de novo seed. TTL de checkpoint até próximo reseed do modo, máx. 30 dias.  
- **Observabilidade**: OTEL (traces/metrics/logs JSON) com labels tenant/ambiente/seed_run_id/manifest_version; redaction PII (ADR-010); spans de lote e de validação de manifesto; erro no export marca run como failed.  
- **Relatório WORM**: Ao final (ou falha), gerar relatório JSON assinado (hash/assinatura) com manifest/tenant/ambiente, trace/span IDs, volumetria prevista/real, uso de rate limit/budget, SLO atingidos, erros Problem Details; armazenar em WORM (ex.: S3 Object Lock) com retenção mínima 1 ano e integridade verificada; indisponibilidade de WORM → abort antes de escrever dados.  
- **Limpeza/expurgo**: Modos carga/DR limpam dataset do modo antes de recriar; TTL de datasets de carga/DR executado via Argo CronJob; dry-run não persiste checkpoints nem WORM.

### Manifesto `seed_profile` — schema v1 (canary opcional)

- **Fonte**: Manifestos versionados em `configs/seed_profiles/<ambiente>/<tenant>.yaml` (GitOps/Argo CD). JSON Schema v1 a publicar em `contracts/seed-profile.schema.json` (JSON Schema 2020-12) e usado pelo endpoint `/api/v1/seed-profiles/validate`.  
- **Campos obrigatórios**:  
  - `metadata`: `tenant`, `environment`, `profile`, `version` (SemVer), `schema_version`, `salt_version`, `reference_datetime` (ISO 8601 UTC).  
  - `mode`: `baseline|carga|dr`; `window.start_utc/end_utc` (par único, UTC, pode cruzar meia-noite).  
  - `volumetry`: caps Q11 por entidade; `rate_limit` (`limit`, `window_seconds`), `backoff` (`base_seconds`, `jitter`, `max_retries`), `budget` (`cost_cap`, `error_budget`), `ttl` por modo.  
  - `slo`: `p95_target_ms`, `p99_target_ms`, `throughput_target`.  
  - `canary`: obrigatório somente quando `mode=canary` (percentual ou tenants-alvo).  
- **Regras**: Versão nova de `reference_datetime` é breaking e exige reseed/limpeza de checkpoints; schema_version divergente → fail-closed; overrides só permitidos em dev isolado.  
- **Evidência**: Manifesto e hash de integridade referenciados no relatório WORM e no `SeedRun.profile_version`.

#### Detalhamento normativo do JSON Schema v1 (para remover ambiguidades)
- **Dialeto**: JSON Schema 2020-12 com `jsonSchemaDialect` declarado; validação fail-closed (sem defaults implícitos).  
- **`volumetry`**: objeto de entidades (`<entity>` → `{cap: integer >=1, target_pct: number 0-100 opcional}`); rejeitar chaves fora do catálogo suportado; unidades sempre em contagem de registros.  
- **`rate_limit`**: `{limit: integer >=1, window_seconds: integer >=1, burst: integer >= limit opcional}`; `RateLimit-Reset` deriva de `window_seconds`.  
- **`backoff`**: `{base_seconds: integer >=1, jitter_factor: number 0.0-1.0, max_retries: integer >=0, max_interval_seconds: integer >= base_seconds}`; fórmula: `sleep = min(max_interval_seconds, base_seconds * 2^attempt) * random(1 - jitter_factor, 1 + jitter_factor)`.  
- **`budget`**: `{cost_cap_brl: number >=0 com 2 casas, error_budget_pct: number 0-100}`; alerta em 80% e abort em 100%.  
- **`slo`**: `{p95_target_ms: integer >=1, p99_target_ms: integer >=1, throughput_target_rps: number >=0.1}`.  
- **`ttl`**: `{baseline_days: integer >=0, carga_days: integer >=0, dr_days: integer >=0}`.  
- **`canary`**: `{percentage: number 0-100} ou {tenants: array string unique, minItems=1}`; obrigatório somente quando `mode=canary`.  
- **`reference_datetime`**: ISO 8601 UTC obrigatório; mudança é breaking.  
- **`integrity`**: campos `manifest_hash` (sha256 hex) e `schema_version` devem coincidir com o schema publicado; divergência falha.  
- **Exemplos**: incluir exemplos canônicos por modo no schema para servir de goldens de lint/diff.  
- **Contrato**: publicar em `contracts/seed-profile.schema.json` e referenciar em `/api/v1/seed-profiles/validate` e CI (Spectral + oasdiff).  

### Catálogo de volumetria → modelos/serializers
- **Chaves válidas** (alinhar com `seed-profile.schema.json`): `tenant_users`, `customers`, `addresses`, `consultants`, `bank_accounts`, `account_categories`, `suppliers`, `loans`, `installments`, `financial_transactions`, `limits`, `contracts`. Nenhuma outra chave é aceita.  
- **Mapeamento**:  
  - `tenant_users` → `backend/apps/tenancy/models/user.py` (AbstractUser com FK `tenant_id`; username/email únicos por tenant; seeds geram service accounts para RBAC).  
  - `customers` → `backend/apps/banking/models/customer.py` (DDL detalhado abaixo; `document_number` pgcrypto+FPE, único por tenant).  
  - `addresses` → `backend/apps/banking/models/address.py` (FK para `Customer`, campos CEP/UF; `is_primary` bool).  
  - `consultants` → `backend/apps/banking/models/consultant.py` (OneToOne `User`, `balance` decimal(10,2)).  
  - `bank_accounts` → `backend/apps/banking/models/bank_account.py` (campos `name`, `agency`, `account_number`, `initial_balance` decimal(15,2); status/type definidos neste plano).  
  - `account_categories` → `backend/apps/banking/models/account_category.py` (catálogo `code`/`description` por tenant, derivado de `PaymentCategory` do blueprint).  
  - `suppliers` → `backend/apps/banking/models/supplier.py` (`document_number` FPE, unicidade opcional por tenant).  
  - `loans` → `backend/apps/banking/models/loan.py` (status enum `IN_PROGRESS|PAID_OFF|IN_COLLECTION|CANCELED`, campos regulatórios CET/IOF).  
  - `installments` → `backend/apps/banking/models/installment.py` (status enum `PENDING|PAID|OVERDUE|PARTIALLY_PAID`, FK `loan`).  
  - `financial_transactions` → `backend/apps/banking/models/financial_transaction.py` (enum `INCOME|EXPENSE`, FKs opcionais para category/cost_center/supplier/installment).  
  - `limits` → `backend/apps/banking/models/credit_limit.py` (DDL abaixo; vinculado a `BankAccount`).  
  - `contracts` → `backend/apps/banking/models/contract.py` (ETag/If-Match, PII mascarada).  
- **Ordem/dag** (batches): `tenant_users -> customers -> addresses -> consultants -> bank_accounts -> account_categories -> suppliers -> loans -> installments -> financial_transactions -> limits -> contracts`.  
- **Serializers**: DRF serializers nos mesmos paths validam tipos/enums/precisão decimal e são reutilizados pelas factories.

### Alinhamento CLI x API

- **CLI (`manage.py seed_data`)**: Caminho primário para execuções controladas (CI/PR dry-run, staging carga/DR). Orquestra locks, criação de `SeedRun/SeedBatch`, chamadas Celery e relatório WORM.  
- **API `/api/v1/seed-runs*`**: Usada para agendar/cancelar/consultar execuções de forma remota (Argo/CD/portais internos); retorna RateLimit-*, Idempotency-Key e ETag/If-Match; reutiliza mesma camada de serviço da CLI.  
- **Contrato/serviço único**: Serviços de aplicação em `backend/apps/tenancy/services/seed_runs.py` (a criar) expostos tanto via CLI quanto via API para evitar divergência; checkpoints/idempotência persistidos sempre no banco com RLS.

#### Contrato mínimo para `/api/v1/seed-runs*` (alinhado ao ADR-011)
- **POST `/api/v1/seed-runs`**: cria execução. Payload: `{manifest_path, mode, dry_run?, idempotency_key, canary?}`; headers obrigatórios: `Idempotency-Key`, `X-Tenant-ID`, `X-Environment`; resposta `201` com `Location`, `ETag`, `RateLimit-*`, body com `seed_run_id`, `status`, `manifest_hash`. Erros: `401/403`, `409` se lock ativo, `422` Problem Details (schema/manifest), `429` com `Retry-After`.  
- **GET `/api/v1/seed-runs/{id}`**: consulta status. Headers: `If-None-Match` opcional; respostas `200` com estado completo + checkpoints, ou `304` quando ETag casar.  
- **POST `/api/v1/seed-runs/{id}/cancel`**: requer `If-Match` + `Idempotency-Key`; respostas `202` (cancel agendado) ou `409` se status terminal.  
- **Errors**: Problem Details com `type`, `title`, `detail`, `instance`, `status`, `violations[]`; sempre enviar `RateLimit-*` e `Retry-After` em `429`.  
- **Pact/OpenAPI**: paths acima devem constar em `contracts/seed-data.openapi.yaml` com exemplos e schemas referenciando `seed-profile.schema.json`.
- **Idempotência (Art. XI / ADR-011 / runbook de governança)**: `Idempotency-Key` persiste em `tenancy_seed_idempotency` com deduplicação por `key_hash+payload_hash+tenant+environment`, TTL mínimo de 24h (configurável por modo via manifesto) e `response_snapshot`; replays retornam a mesma resposta e são auditados (OTEL + relatório WORM). Limpeza periódica (cron/Celery beat) remove expirados.

#### Máquina de estados (SeedRun/SeedBatch)
- **SeedRun**: `queued -> running -> {succeeded | failed | aborted}`; `running -> retry_scheduled` em erro transitório e retorna a `running` após backoff; `running -> blocked` (lock/maintenance/off-peak fechada) e encerra em `aborted` após timeout; cancelamento via endpoint (`If-Match`) seta flag `cancel_requested` e finaliza como `aborted` após drenar/parar os batches. `retry_scheduled` não avança para `succeeded` sem novo `ETag`.  
- **SeedBatch**: `pending -> processing -> {completed | failed}`; `processing -> retry_scheduled` em 429/erro transitório com jitter; `retry_scheduled -> processing` até `max_retries`; excedeu → `dlq`; `dlq` só volta a `processing` por ação operacional (Argo/CD) registrada em auditoria. Status `failed/dlq` bloqueiam `SeedRun` se não houver batch subsequente aberto.

### IaC, GitOps e OPA (Art. XIV)
- Recursos de seeds/factories (Vault Transit keys/roles, filas Celery/Redis, buckets WORM com Object Lock, roles seed-runner e pipelines Argo CD) são versionados em `infra/` via Terraform.  
- Policies OPA/Gatekeeper validam naming/tagging, RLS habilitado, Object Lock ativo e ausência de snapshots/dumps de produção; pipelines de `terraform plan` + `opa test` são gates de CI.  
- Argo CD aplica drift detection e rollback automatizado; promoções respeitam janela off-peak do manifesto e bloqueiam se drift, policy ou checklist de aprovação falhar.

### Observabilidade, FinOps e rate limit

- **Rate limit/FinOps**: Manifesto define caps; calcular consumo e alertar em 80% do budget; abort/rollback em 100% (fail-closed). Propagar cabeçalhos `RateLimit-*`/`Retry-After` em API e logs de CLI; registrar consumo no relatório WORM. Cálculo de custo: estimativa = (requests API * custo_unit_request + CPU_s * custo_unit_CPU + GB_s Redis/DB * custo_unit_storage); custo real = amostragem Prometheus/CloudWatch por SeedRun. Janela de apuração = por SeedRun + agregação diária por ambiente/tenant; registrar `cost_model_version` e fonte de preços/metas no relatório e tabela de budget.  
- **SLO**: Medir p95/p99 de execução por manifesto e throughput por lote; violação consome error budget e pode abortar.  
- **Telemetria**: Conformidade com ADR-012 (OTEL + Sentry) e ADR-010 (redação PII). Falha de export → marca SeedRun como failed e bloqueia promoção (Art. VII).  
- **PII**: FPE determinística via Vault Transit (FF3-1/FF1), chaves/salts por ambiente/tenant com rotação trimestral; fallback apenas em dev isolado; pgcrypto em repouso; catálogo PII aplicado nas factories.
- **DORA/flags**: métricas DORA (lead time, MTTR, frequency) coletadas no pipeline; feature flags/canary são obrigatórios e testados em rollback antes da promoção.

#### FinOps — fonte de preços e fórmula
- **Catálogo de preços**: versionar em `configs/finops/seed-data.cost-model.yaml` com `cost_model_version` SemVer e origem (AWS/GCP preço on-demand). Itens mínimos: `cpu_second_brl`, `db_io_gb_brl`, `redis_cmd_1k_brl`, `api_request_brl`.  
- **Estimativa**: `cost_estimated_brl = cpu_seconds*cpu_second_brl + db_io_gb*db_io_gb_brl + redis_cmd_1k*redis_cmd_1k_brl + api_requests*api_request_brl`; `db_io_gb = (pg_read_bytes + pg_write_bytes)/1e9`.  
- **Métricas fonte**: Prometheus `celery_task_cpu_seconds_total`, `postgresql_io_bytes_total`, `redis_commands_processed_total`, `seed_api_requests_total` exportada pelo serviço. Janela por `SeedRun` + agregação diária (`cost_window_started_at/cost_window_ends_at`). Alertas em ≥80% e abort em ≥100% (fail-closed) conforme `docs/pipelines/ci-required-checks.md`.  
- **Registro**: persistir `cost_model_version`, `cost_estimated_brl`, `cost_actual_brl` em `BudgetRateLimit` e relatório WORM; CI dry-run grava artifact em `artifacts/perf/seed-finops.json`.
- **Schema YAML (cost-model)**:  
  ```yaml
  cost_model_version: "1.0.0"        # SemVer obrigatório
  provider: aws                      # enum: aws|gcp|azure
  region: sa-east-1                  # string obrigatória
  currency: BRL                      # default BRL; múltiplos de 0.01
  cpu_second_brl: 0.0008             # número >=0, 4 casas
  db_io_gb_brl: 0.12                 # número >=0, 2 casas
  redis_cmd_1k_brl: 0.003            # número >=0, 3 casas
  api_request_brl: 0.0004            # número >=0, 4 casas
  notes: "on-demand baseline nov/2025" # opcional
  ```  
  Falhar fail-closed se campo obrigatório estiver ausente/negativo ou precisão fora do dialeto acima. CI valida via JSON Schema em `contracts/finops/seed-data.cost-model.schema.json` (artefato desta feature) e referência é incluída no relatório WORM.

#### Perf/gate k6
- **Script**: `observabilidade/k6/seed-data-smoke.js` com cenários `validate_manifest`, `create_seed_run`, `poll_seed_run`.  
- **Cargas**: baseline 5 VUs/30s, carga 20 VUs/60s (somente staging/perf), respeitando headers `X-Tenant-ID`/`X-Environment` e `Idempotency-Key` randômica.  
- **Load/DR real**: cenário adicional `seed_load_dr` em `observabilidade/k6/seed-data-load.js` exercita criação/poll de runs e geração de batches com caps Q11/rate-limit e throughput-alvo; aplica thresholds de p95/p99/erro e consumo de budget.  
- **Thresholds**: carregados do manifesto (`slo.p95_target_ms`, `slo.p99_target_ms`, `slo.throughput_target`, `budget.error_budget_pct`, `rate_limit`) e aplicados em tempo de execução; defaults só valem para dev local quando o manifesto declara explicitamente os mesmos valores de referência (validate 800ms, create 1200ms, load_dr 1500ms, erro <1%). Se o manifesto não trouxer thresholds, o pipeline falha (fail-closed). Artefatos JSON: `artifacts/perf/k6-seed-smoke.json` e `artifacts/perf/k6-seed-load.json`, enviados a WORM com assinatura única (hash + assinatura assimétrica) conforme Art. XVI/ADR-011.

#### Regras operacionais de FinOps/Rate Limit
- **Fontes de custo**: estimativa usa catálogo de preços versionado (`cost_model_version`) e métricas OTEL/Prometheus (`seed_run_duration_ms`, `seed_batch_latency_ms`, `celery_task_cpu_seconds_total`, `postgresql_table_size_bytes`); custo real coleta CPU/memória/IO via Prometheus e requests API via `seed_rate_limit_remaining`.  
- **Janela**: cálculo por `SeedRun` e janela diária (`cost_window_started_at/ends_at` em `BudgetRateLimit`). Reset de rate-limit segue `rate_limit.window_seconds`; cabeçalho `RateLimit-Reset` deriva desse campo.  
- **Alertas/abortos**: alerta ao atingir 80% (`budget_alert_at_pct`), aborta em 100% ou `rate_limit_remaining < 0` (fail-closed) com Problem Details `finops_budget_exceeded`.  
- **Logs/relatório**: registrar `cost_model_version`, `cost_estimated_brl`, `cost_actual_brl` e fontes (`prometheus://...`) no relatório WORM e em `BudgetRateLimit`.
- **Catálogo e schema de custo**: publicar `configs/finops/seed-data.cost-model.yaml` e `contracts/finops/seed-data.cost-model.schema.json` (JSON Schema 2020-12); CI valida ambos e falha fail-closed se ausentes ou com versão incompatível. FinOps em SeedRun/SeedBatch exige `cost_model_version` obrigatório antes de iniciar carga/DR.

#### Parâmetros operacionais adicionais
- **Celery/Redis**: filas dedicadas `seed_data.default` (baseline) e `seed_data.load_dr` (carga/DR); DLQ `seed_data.dlq`. Prefetch 1, `acks_late=True`, `visibility_timeout` = `max_interval_seconds * 2`. Paralelismo por worker: baseline 1, carga/DR até 4.  
- **Backoff/jitter**: usar `retry_backoff=True`, `retry_backoff_max = max_interval_seconds` e jitter multiplicativo `random(1 - jitter_factor, 1 + jitter_factor)`; aplicar também para 429.
- **Locks**: advisory lock global = `hashtext('seed_data:global:'||environment)`; por tenant = `hashtext('seed_data:'||tenant||':'||environment)`, com lease 60s; fila auditável em tabela `tenancy_seed_queue` com TTL 5 min.
- **Relatório WORM**: payload JSON com campos obrigatórios `{run_id, tenant, environment, manifest_path, manifest_hash_sha256, schema_version, mode, reference_datetime, caps, rate_limit_usage, budget_usage, batches[], checkpoints[], errors[], otel_trace_id, otel_span_id, started_at, finished_at, outcome, cost_model_version, cost_estimated_brl, cost_actual_brl}`; `signature_hash` = `sha256` do payload; assinatura assimétrica via KMS/Vault (`signature_algo` = `RSA-PSS-SHA256` ou `Ed25519`) armazenada em `signature` com `key_id`/`key_version`. Destino: bucket S3 Object Lock `worm/seeds/<env>/<tenant>/<run_id>.json`, retenção mínima 365 dias; verificar assinatura após upload e antes de marcar `integrity_status=verified`, com retry exponencial (máx. 3) em upload/verify.
- **Observabilidade mínima**: spans nomeados `seed.run`, `seed.batch`, `seed.manifest.validate`; atributos obrigatórios `tenant_id`, `environment`, `seed_run_id`, `manifest_version`, `mode`, `dry_run`; métricas `seed_run_duration_ms` (histogram), `seed_batch_latency_ms` (histogram), `seed_rate_limit_remaining`, `seed_budget_remaining`; logs JSON com `level`, `event`, `tenant_id`, `seed_run_id`, `pii_redacted=true`. Export falho → status `failed` com Problem Details `telemetry_unavailable`. Gate de SLO/error budget roda em tempo de execução: se p95/p99/throughput excederem thresholds do manifesto, aborta ou reagenda off-peak, registrando Problem Details e checklist no relatório WORM.  
- **Assinatura/WORM operacional**: cliente Python `boto3` com `ObjectLockMode=COMPLIANCE` e `RetainUntilDate` ≥ 365 dias; assinatura via Vault Transit path `transit/sign/seeds-worm` (key `seed-worm-report`) ou KMS equivalente por ambiente (`arn:aws:kms:...:key/seeds-worm`). Passos: (1) calcular `signature_hash`; (2) `vault write transit/sign/seeds-worm hash=<signature_hash>`; (3) upload com metadados `x-seeds-signature`, `x-seeds-key-id`; (4) verificar via `transit/verify` após upload. Falha em qualquer passo → abortar `SeedRun`.  
- **Checklist automatizado**: relatório WORM inclui percentuais e resultados de checklist PII/RLS/contratos/idempotência/rate-limit/SLO; qualquer reprovação marca o run como `failed` e bloqueia promoção/Argo CD.

#### Operacional WORM/OTEL (ambientes e fallback)
- **Buckets e segredos**: variáveis `SEEDS_WORM_BUCKET`, `SEEDS_WORM_ROLE_ARN`, `SEEDS_WORM_KMS_KEY_ID`, `SEEDS_WORM_RETENTION_DAYS` (>=365) por ambiente; tempo limite de upload/verificação 10s, payload máximo 5 MB. Ambientes que exigem WORM (staging/perf) falham fail-closed se bucket/KMS/Vault estiverem indisponíveis ou se a verificação de assinatura não concluir; não há fallback. Dry-run/CI que não escrevem WORM pulam o passo de upload.  
- **OTEL**: `OTEL_EXPORTER_OTLP_ENDPOINT` obrigatório; headers `x-otlp-tenant`/`x-otlp-environment` configurados; `OTEL_TRACES_SAMPLER=parentbased_always_on` em prod/staging, `parentbased_traceidratio(0.05)` em CI. Timeout export 5s; falha de export marca run como `failed` (Problem Details `telemetry_unavailable`) conforme ADR-012/runbook `docs/runbooks/observabilidade.md`.  
- **Sentry**: DSN por ambiente e `traces_sample_rate` alinhada ao sampler OTEL; captura de PII desabilitada.  
- **Fallback**: qualquer indisponibilidade de Vault/KMS/WORM/OTEL fora de dev-isolado aborta antes de escrever dados (Art. XVI, ADR-010/012).

#### Fila global e GC (`SeedQueue`)
- Inserção em `tenancy_seed_queue` ocorre antes do lock global; registros `pending` expiram em 5 min (`expires_at`).  
- Job Argo Cron (`seed-queue-gc`, a cada 1 min) limpa `status=expired` e audita; se ambiente tiver >2 execuções ativas, marca excedentes como `expired` e retorna `Problem Details global_concurrency_cap`.  
- `lease_lock_key` deve bater com o advisory lock vigente; mismatch entre lock e fila → fail-closed e reaplica lock antes de reprocessar.

#### Parâmetros por ambiente e FinOps (assunções consolidadas do clarify)
- **Volumetria Q11 por ambiente**: dev 1x baseline, homolog 3x, staging/carga 5x (staging dedicado para carga/DR); caps por entidade versionados no manifesto. Não executar carga/DR em produção/controlada.
- **Rate limit alvo (RPM)**: dev 300, homolog 600, staging/carga 1.200; usar no máximo 80% do limite e aplicar backoff+jitter ao se aproximar do cap.
- **Tempos-alvo por ambiente**: dev <5 min, homolog <10 min, staging/carga <20 min; exceder +20% aborta/rollback auditado.
- **Budget por execução (FinOps)**: dev/homolog até US$5, staging/carga até US$25; alertar em 80%, abortar em 100% (fail-closed) e exigir ajuste do manifesto.
- **Dry-run em CI/PR**: apenas baseline determinístico para um tenant canônico (ou lista curta declarada), sem WORM, validando PII/contrato/idempotência/rate-limit.
- **RPO/RTO**: campanhas carga/DR devem comprovar RPO ≤5 min e RTO ≤60 min em staging/perf com manifesto canônico; execuções fora de staging ou sem evidência WORM assinada falham em fail-closed e não são promovidas.

#### Tabela canônica de caps Q11 (por entidade, antes de multiplicadores de ambiente)

| Entidade                | Baseline cap | Carga cap | DR cap |
|-------------------------|--------------|-----------|--------|
| tenant_users            | 5            | 10        | 10     |
| customers               | 100          | 500       | 500    |
| addresses               | 150          | 750       | 750    |
| consultants             | 10           | 30        | 30     |
| bank_accounts           | 120          | 600       | 600    |
| account_categories      | 20           | 60        | 60     |
| suppliers               | 30           | 150       | 150    |
| loans                   | 200          | 1_000     | 1_000  |
| installments            | 2_000        | 10_000    | 10_000 |
| financial_transactions  | 4_000        | 20_000    | 20_000 |
| limits                  | 100          | 500       | 500    |
| contracts               | 150          | 750       | 750    |

Multiplicadores por ambiente (aplicados sobre a tabela acima): dev = 1x, homolog = 3x, staging/carga = 5x (staging dedicado), perf = 5x. Proibido carga/DR em produção/controlada.

#### Bloqueio de mutações e caches
- **Caches/índices/busca**: invalidar caches Redis e rebuild de busca/índices em torno da execução; rebuild só em modos controlados (dry-run/staging/carga/DR), proibido em produção fora da janela aprovada para preservar determinismo/idempotência.
- **Eventos/outbox/CDC**: sempre roteados para sinks sandbox com mocks/stubs e auditoria; nunca publicar em destinos reais durante seeds/factories/carga/DR.
- **Enforcement de janela off-peak**: preflight do CLI/API valida `now() AT TIME ZONE 'UTC'` contra `SeedProfile.window` e `tenancy_tenant.off_peak_window_utc`; fora da janela marca `SeedRun` como `blocked` com Problem Details `offpeak_window_closed`. Middleware DRF adicional impede POST/PUT de domínios afetados quando a janela estiver fechada, registrando auditoria.

#### RBAC/ABAC e gate RLS/off-peak
- **Policies**: versionar matriz em `configs/rbac/seed-data.yaml` com perfis `seed-runner` (execução), `seed-admin` (cancel/reprocess), `seed-read` (consulta). Binding por `tenant`, `environment` e `subject` (service account). Registrar cópia no banco (`tenancy_seed_rbac`) para auditoria e aplicar via permission class DRF `SeedDataPermission`.  
- **ABAC**: regras mínimas: ambiente permitido, janela off-peak ativa, tenant com `maintenance_mode=true` para domínios afetados, flag/canary habilitado; negar se qualquer regra falhar.  
- **RLS gate**: middleware DRF `RLSPreflightMiddleware` confirma `SET app.tenant_id` aplicado e policies de `backend/apps/tenancy/sql/rls_policies.sql` carregadas; CLI reusa o mesmo serviço e aborta com código 6 (quickstart) se falhar.  
- **Headers obrigatórios**: `X-Tenant-ID`, `X-Environment`, `Idempotency-Key`, `If-Match` nos cancelamentos; ausência de condicional em mutações retorna `428` (ADR-011/runbook governança de API).  
- **Auditoria**: cada decisão de RBAC/ABAC e bloqueio off-peak registra `Problem Details` e span OTEL com `auth.result` (`allow|deny`) e `auth.policy_version`.
- **Testes negativos**: suites CLI/API devem negar perfis seed-read/fora do escopo, tenants/ambientes proibidos e janela off-peak fechada, com evidência automatizada no CI.
- **Matriz de permissões (estável)**:  
  - `seed-runner`: cria `SeedRun` (CLI/API), executa dry-run, lê status do próprio tenant/ambiente; não cancela execuções nem toca DLQ.  
  - `seed-admin`: inclui permissões de runner + cancelar (`POST /seed-runs/{id}/cancel`), reprocessar batches DLQ, ajustar `maintenance_mode` do tenant durante janela off-peak.  
  - `seed-read`: somente leitura (`GET /seed-runs/{id}`, `GET /seed-profiles/validate` dry-run).  
  - Binding obrigatório em `configs/rbac/seed-data.yaml` por `tenant`+`environment`; ausência ou mismatch → `403` fail-closed.  
  - Todas as tabelas novas (`tenancy_seed_*` e `banking_*`) recebem `POLICY tenant_id = current_setting('app.tenant_id')::uuid` com managers aplicando `tenant_id` por padrão, seguindo `BaseTenantModel` do blueprint.

### Cobertura de entidades e factories

- **Escopo mínimo**: tenants/usuários, clientes/endereços, consultores, contas bancárias/categorias/fornecedores, empréstimos/parcelas, transações financeiras, limites/contratos (conforme clarificações).
- **Factories**: factory-boy determinísticas (seed derivado de tenant/ambiente/manifesto), mascaramento PII obrigatório, compatíveis com serializers `/api/v1`; validam CET/IOF/parcelas contra serviços oficiais.
- **Baseline vs carga/DR**: Baseline somente happy paths/estados ativos; carga/DR incluem estados bloqueado/inadimplente/cancelado com percentuais por entidade no manifesto; reexecução limpa datasets do modo antes de recriar.

#### Catálogo PII e seed determinístico
- **PII por entidade**: `Customer` (document_number, name, email, phone, address fields), `Consultant` (name, phone, email), `Supplier` (name, document_number), `FinancialTransaction` (description se contiver PII, reference), `Loan`/`Installment` (customer-linked identifiers).  
- **Máscara/anonimização**: usar `vault_transit_ff3-1` preservando formato (CPF/CNPJ/telefone/email) para todos os campos acima; pgcrypto em repouso.  
- **Seed determinístico**: `factory_seed = sha256(tenant_id || environment || manifest_version || salt_version)` truncado para inteiro; todas as factories usam esse seed via helper central.  
- **Cálculo CET/IOF/parcelas**: sempre chamar serviços/domínio oficiais; validar igualdade arredondada a 2 casas; divergência falha o lote.  
- **Ambientes**: fallback de FPE somente em dev isolado com chave em `.env.local`; CI/staging/prod falham se fallback ativo.
- **Vault Transit PII**: paths `transit/seeds/<environment>/<tenant>/ff3` para FPE e `transit/seeds/<environment>/<tenant>/ff1` para formatos legados; role `seed-data` com política de mínimo privilégio. Helper `get_fpe_client(env, tenant, salt_version)` retorna callable injetado nas factories; falha de autorização → fail-closed.  
- **Catálogo de campos/estados (baseline/carga/DR)**:  
  - `customers`: baseline 100% `ACTIVE`; carga/DR adicionam 10% `BLOCKED`, 10% `DELINQUENT`, 5% `CANCELED`. PII mascarada em `document_number`, `email`, `phone`, `address.*`.  
  - `bank_accounts`: baseline `ACTIVE`; carga/DR com 5% `BLOCKED`. Campos sensíveis: `account_number`, `branch/agency`.  
  - `loans`: baseline status `IN_PROGRESS`; carga/DR com `IN_COLLECTION` 20% e `CANCELED` 10%.  
  - `installments`: derivadas de loans, datas fixadas a partir de `reference_datetime` para determinismo.  
  - `financial_transactions`: descrições sintéticas sem PII; 5% reversões em carga/DR.  
  - `limits/contracts`: contratos simulados assinados com ETag derivado do payload e PII mascarada em identificadores.

#### Serviço de cálculo CET/IOF/parcelas (contrato único)
- **Implementação**: serviço puro em `backend/apps/banking/services/financial_calculations.py` com funções `calculate_iof(request: LoanInput) -> Decimal`, `calculate_cet(request: LoanInput) -> CETBreakdown`, `generate_installments(request: LoanInput) -> list[InstallmentInput]`.  
- **Entrada (`LoanInput`)**: `{principal_amount: Decimal(12,2), annual_rate_pct: Decimal(5,2), number_of_installments: int>0, contract_date: date, first_installment_date: date, tenor_months opcional}`; datas derivam de `reference_datetime` do manifesto.  
- **Saída (`CETBreakdown`)**: `{cet_annual_rate: Decimal(7,4), cet_monthly_rate: Decimal(7,4), iof_amount: Decimal(10,2), installments: list[InstallmentInput]}`.  
- **Stubs de teste**: Pact stubs em `contracts/pacts/financial-calculator.json` (a criar) com exemplos determinísticos; usados por factories e testes de integração dos endpoints de seeds.  
- **Fail-closed**: divergência entre retorno do serviço e cálculo esperado (duas casas para valores, quatro casas para taxas) aborta o lote. Fallback local permitido apenas em dev isolado com fixtures do stub.

#### Mapeamento para models/serializers reais (novo app de domínio)
- **App**: criar `backend/apps/banking/` com models + serializers DRF, managers com `TenantManager` e RLS ativa (Art. XIII). Factories em `backend/apps/banking/tests/factories.py` reutilizam os serializers para validar contratos `/api/v1`.  
- **Customer**: `id UUID PK`, `tenant_id` FK, `name` varchar(255), `document_number` char(20) com pgcrypto+FPE, `birth_date` date null, `email` EmailField null, `phone` char(20) null, `status` enum `ACTIVE|BLOCKED|DELINQUENT|CANCELED` (default `ACTIVE`), `created_at/updated_at` audit. `unique(tenant_id, document_number)`. Serializer redige PII e aplica status conforme catálogo.  
- **Address**: `customer_id` FK, `zip_code` char(10), `street` varchar(255), `number` varchar(20), `complement` varchar(100) opcional, `neighborhood` varchar(100), `city` varchar(100), `state` char(2), `is_primary` bool default false. Index `unique(customer_id, is_primary WHERE is_primary)` opcional para garantir um endereço principal.  
- **Consultant**: `user` OneToOne `tenancy_user`, `balance` decimal(10,2) default 0.00; herdado de BaseTenantModel.  
- **BankAccount**: `name` varchar(100), `agency` char(10) (FPE), `account_number` char(20) (FPE), `initial_balance` decimal(15,2) default 0.00, `type` enum `CHECKING|SAVINGS`, `status` enum `ACTIVE|BLOCKED` default `ACTIVE`, FK `customer`. `unique(tenant_id, account_number)` e `unique(tenant_id, agency, account_number)` (ver blueprint).  
- **AccountCategory**: catálogo por tenant (`code` varchar(40), `description` varchar(255), `is_default` bool); `unique(tenant_id, code)`; deriva de `PaymentCategory` do blueprint, sem PII.  
- **Supplier**: `name` varchar(255), `document_number` char(20) FPE (null/blank permitido), `status` enum `ACTIVE|BLOCKED` default `ACTIVE`; índice `unique(tenant_id, document_number)` quando não nulo.  
- **Loan**: `customer_id` FK (PROTECT), `consultant_id` FK (PROTECT), `principal_amount` decimal(12,2), `interest_rate` decimal(5,2) (taxa mensal), `number_of_installments` smallint, `contract_date` date, `first_installment_date` date, `status` enum `IN_PROGRESS|PAID_OFF|IN_COLLECTION|CANCELED` (default `IN_PROGRESS`), `iof_amount` decimal(10,2), `cet_annual_rate` decimal(7,4), `cet_monthly_rate` decimal(7,4). Índice `index(tenant_id, status)` e `index(tenant_id, customer_id)`.  
- **Installment**: `loan_id` FK (CASCADE), `installment_number` smallint, `due_date` date, `amount_due` decimal(10,2), `amount_paid` decimal(10,2) default 0.00, `payment_date` date null, `status` enum `PENDING|PAID|OVERDUE|PARTIALLY_PAID` (default `PENDING`). Índice `unique(loan_id, installment_number)`.  
- **FinancialTransaction**: `description` varchar(255), `amount` decimal(12,2), `transaction_date` date, `is_paid` bool default false, `payment_date` date null, `type` enum `INCOME|EXPENSE`, FKs opcionais `bank_account` (PROTECT), `category` (SET NULL), `cost_center` (SET NULL), `supplier` (SET NULL), `installment` (SET NULL, related_name payments).  
- **CreditLimit** (`limits`): `bank_account_id` FK, `current_limit` decimal(12,2), `used_amount` decimal(12,2) default 0.00, `status` enum `ACTIVE|FROZEN|CANCELED` (default `ACTIVE`), `effective_from/through` daterange opcional; `unique(tenant_id, bank_account_id)`.  
- **Contract** (`contracts`): `bank_account_id` FK opcional, `customer_id` FK opcional, `body` JSONB (payload assinado), `etag_payload` sha256 hex (usada em ETag/If-Match), `version` SemVer, `signed_at` timestamptz, `status` enum `ACTIVE|REVOKED|EXPIRED`, PII mascarada antes de assinar. `unique(tenant_id, etag_payload)`.

#### Checkpoints e idempotência — detalhamento
- **hash_estado**: `sha256` de JSON canônico ordenado `{entity, batch_seq, manifest_hash_sha256, last_pk, caps_snapshot}`.  
- **resume_token**: JSON `{entity, batch_seq, last_pk, factory_seed}` criptografado via `pgp_sym_encrypt` com chave `seed_resume_key` provisionada via Vault (envelope) e armazenado em `bytea`.  
- **Retomada**: na retomada, descriptografar `resume_token`, validar `hash_estado` contra manifesto/`SeedBatch`; divergência → abortar e exigir limpeza de checkpoints.  
- **Persistência determinística**: IDs gerados via UUIDv5 namespaced (`tenant|entity|batch_seq|manifest_version`) para dedupe sem expor PII.

#### Idempotency-Key, ETag e locks → HTTP
- **Store de idempotência**: criar tabela `tenancy_seed_idempotency` (RLS) com `(tenant_id, environment, idempotency_key, manifest_hash_sha256, mode, seed_run_id, expires_at)` e TTL padrão 24h (GC via Argo Cron). CLI e API compartilham serviço único (`backend/apps/tenancy/services/seed_idempotency.py`); conflito de chave com `manifest_hash` divergente retorna `409` Problem Details `idempotency_conflict`, mesma chave/manifesto devolve run existente. `/api/v1/seed-profiles/validate` reutiliza o mesmo serviço/armazenamento (TTL 24h) para dedupe e replay determinístico (retorna a mesma resposta 200/422/429), bloqueando conflitos de manifesto com 409.  
- **ETag/versão**: `SeedRun` recebe coluna `row_version` (bigint) incrementada a cada mudança; ETag = `W/"<row_version>"`. `POST /seed-runs/{id}/cancel` e demais mutações exigem `If-Match`; ausência → `428 Precondition Required` (ADR-011/runbook governança de API).  
- **Locks → HTTP**: lock/advisory ativo ou fila acima do teto global respondem `409` (`seed_run_locked`), rate-limit/budget `429` com `Retry-After`, dependência (Vault/WORM/fila) `503` com `Retry-After`. Middleware/permission DRF aplica esses códigos antes de enfileirar; CLI usa os mesmos códigos de saída mapeados (3 para lock, 4 para WORM/telemetria, 5 para rate-limit/budget).

## Threat modeling, runbooks e GameDays (Art. XVII)

- Rodadas STRIDE/LINDDUN específicas para seeds/carga/DR com backlog mitigável e owners em `docs/runbooks/seed-data.md`.  
- GameDay semestral simula 429 persistente, falha de WORM e drift de manifesto; sucesso = RPO ≤ 5 min, RTO ≤ 60 min, zero vazamento cross-tenant e checklist PII/RLS/contratos aprovado.  
- Runbooks incluem bloqueios off-peak, rate-limit, Vault/PII e DR; métricas DORA/SLO exportadas para dashboards e vinculadas aos relatórios WORM.

## Observabilidade e fail-close (Art. VII, ADR-012)

- Exportadores OTEL/Sentry são gating: falha de export ou redaction reprova SeedRun e pipelines CI/Argo; dry-run em CI injeta falha sintética para provar fail-close.  
- Logs/WORM devem incluir labels obrigatórios (`tenant_id`, `environment`, `seed_run_id`, `manifest_version`, `mode`) e ausência de PII; ausência de labels ou PII detectada reprova checklist WORM/logs.  
- Evidências de falha/sucesso são armazenadas em WORM com assinatura e integridade verificada antes de marcar `integrity_status=verified`.

## Complexity Tracking

*Preencha somente quando algum item da Constitution Check estiver marcado como N/A/violado. Cada linha deve citar explicitamente o artigo impactado e o ADR/clarify que respalda a excecao.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| | | |
