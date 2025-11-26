---
description: "Tasks para Automacao de seeds, dados de teste e factories"
---

# Tasks: Automacao de seeds, dados de teste e factories

**Input**: Artefatos em `specs/003-seed-data-automation/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md, tasks.md)  
**Pre-requisitos**: `plan.md` aprovado e pendencias do `/clarify` refletidas em `research.md`  
**Testes (Art. III)**: Escreva testes primeiro e com falha visivel antes da implementacao; mantenha evidencias de vermelho→verde  
**Organizacao**: Tarefas agrupadas por user story para manter fatias verticais independentes e testaveis  
**Formato da linha**: `- [ ] T001 [P] [USx] Descricao (caminho)` — `[P]` so para itens paralelizaveis, `[USx]` apenas em fases de user story

## Fase 1: Setup
Objetivo: Publicar artefatos de contrato/manifesto e comandos base para permitir lint/dry-run desde o inicio.  
Critério de teste independente: contratos e manifestos canônicos passam lint/diff e podem ser usados pelo comando `seed_data` em modo dry-run sem gravação de WORM/checkpoints e com falha OTEL/Sentry forçada sendo bloqueadora.

- [ ] T001 Publicar contratos seed-data e schema para lint/diff (`contracts/seed-data.openapi.yaml`, `contracts/seed-profile.schema.json`)
- [ ] T002 Criar manifestos canônicos baseline/carga/DR por ambiente/tenant (dev/homolog/staging/perf/prod-controlada) validados contra schema v1 (`configs/seed_profiles/<env>/<tenant>.yaml`)
- [ ] T003 Adicionar alvo CI/Makefile para `seed_data` validate/dry-run com Idempotency-Key, sem gravar WORM/checkpoints e falhando em export OTEL/Sentry simulada (`Makefile`, `scripts/ci/seed-data.sh`)
- [ ] T004 Ajustar scripts/Make/CI para lint/diff dos contratos e JSON Schema (Spectral/oasdiff) com paths consolidados (`scripts/ci/validate-seed-contracts.sh`, `Makefile`, `.github/workflows/ci-contracts.yml`)
- [ ] T005 Ajustar scripts Pact/Prism e stub do calculo financeiro para paths dos contratos seed (`scripts/ci/validate-seed-contracts.sh`, `contracts/pacts/financial-calculator.json`)

## Fase 2: Fundacional (bloqueios compartilhados)
Objetivo: Estruturar apps, modelos, politicas RLS/ABAC, utils de determinismo/PII e filas Celery/contract lint.  
Critério de teste independente: migrations e politicas passam testes de modelo/RLS e lint de contratos seed-data roda no CI.

- [ ] T006 Criar e registrar app `banking` nas settings do Django (`backend/apps/banking/apps.py`, `backend/config/settings.py`)
- [ ] T007 Modelar/migrar entidades bancarias com managers RLS (Customer, Address, Consultant, BankAccount, AccountCategory, Supplier, Loan, Installment, FinancialTransaction, CreditLimit, Contract) (`backend/apps/banking/models/*.py`, `backend/apps/banking/migrations/0001_initial.py`)
- [ ] T008 Modelar/migrar tabelas de seeds e auditoria (SeedProfile, SeedRun, SeedBatch, Checkpoint, SeedQueue, SeedDataset, SeedIdempotency, SeedRBAC, BudgetRateLimit, EvidenceWORM) (`backend/apps/tenancy/models/seed_*.py`, `backend/apps/tenancy/migrations/`)
- [ ] T009 Adicionar politicas RLS/ABAC e managers para novas tabelas de seeds (`backend/apps/tenancy/sql/rls_policies.sql`, `backend/apps/tenancy/managers.py`)
- [ ] T010 Implementar helper único de determinismo/idempotencia e cliente Vault Transit FPE reutilizavel para seeds e factories (`backend/apps/foundation/services/seed_utils.py`)
- [ ] T011 Configurar filas Celery/Redis (default, load_dr, dlq) e roteamento para seed_data com acks tardios (`backend/config/settings.py`, `backend/apps/tenancy/tasks.py`, `backend/celery.py`)
- [ ] T012 [P] Testar teto global de concorrencia e TTL da fila (409/429 + reaprazamento) para seeds (`backend/apps/tenancy/tests/test_seed_global_concurrency.py`)
- [ ] T013 Implementar teto global por ambiente/cluster com TTL 5 min na fila e reaprazamento (Problem Details 409/429) (`backend/apps/tenancy/services/seed_runs.py`, `backend/apps/tenancy/services/seed_queue.py`, `backend/apps/tenancy/management/commands/seed_data.py`)
- [ ] T014 Configurar lint/diff de contratos seed-data e JSON Schema no CI (Spectral/oasdiff) (`scripts/ci/validate-seed-contracts.sh`, `package.json`)
- [ ] T015 Criar testes basicos de migracoes/RLS para tabelas banking e seeds (`backend/apps/banking/tests/test_models.py`, `backend/apps/tenancy/tests/test_seed_models.py`)
- [ ] T016 Implementar preflight de disponibilidade Vault/WORM (CLI/API) com fail-close, RBAC/ABAC mínimo e auditoria/redaction de acesso a chaves/manifestos, retornando Problem Details (`backend/apps/tenancy/services/seed_preflight.py`, `backend/apps/tenancy/tests/test_seed_preflight.py`, `infra/`, `docs/runbooks/seguranca-pii-vault.md`)
- [ ] T017 Publicar SLO/SLI/error budget para seed_data e alinhar thresholds do k6 (`docs/slo/seed-data.md`, `observabilidade/k6/seed-data-smoke.js`)
- [ ] T018 Terraform/OPA para Vault/WORM/filas e pipeline Argo CD com drift/rollback e janela off-peak (`infra/`, `scripts/ci/validate-opa.sh`)
- [ ] T019 Garantir migrações expand/contract com índices CONCURRENTLY e testes de rollback (`backend/apps/**/migrations/`, `scripts/ci/check-migrations.sh`)
- [ ] T020 Publicar cost-model FinOps e schema JSON, validar no CI e versionar (`configs/finops/seed-data.cost-model.yaml`, `contracts/finops/seed-data.cost-model.schema.json`, `scripts/ci/validate-finops.sh`)

## Fase 3: User Story 5 - Validar manifestos via API (Prioridade P1)
Objetivo da história: Validar manifestos v1 via API antes de qualquer execução, garantindo schema/versão e governança de headers.  
Critério de teste independente: `POST /api/v1/seed-profiles/validate` retorna 200/422/429 previsíveis com RateLimit-* e Idempotency-Key, sem disparar execução.

### Testes (executar antes da implementacao)
- [ ] T021 [P] [US5] Cobrir 200/422/429 do endpoint `/api/v1/seed-profiles/validate` com headers obrigatorios e Problem Details (`backend/apps/tenancy/tests/test_seed_profile_validate_api.py`)
- [ ] T022 [P] [US5] Cobrir replays de `Idempotency-Key` no `/api/v1/seed-profiles/validate` (TTL 24h; `manifest_hash` divergente retorna 409 `idempotency_conflict`) (`backend/apps/tenancy/tests/test_seed_profile_validate_idempotency.py`)

### Implementacao
- [ ] T023 [US5] Atualizar JSON Schema v1 com caps Q11 obrigatórios por entidade/mode/ambiente e manifestos canônicos alinhados (`contracts/seed-profile.schema.json`, `configs/seed_profiles/<env>/<tenant>.yaml`)
- [ ] T024 [US5] Implementar validador JSON Schema v1 + preflight de manifesto (versao/schema/hash/off-peak) (`backend/apps/tenancy/services/seed_manifest_validator.py`)
- [ ] T025 [US5] Expor `/api/v1/seed-profiles/validate` com RateLimit-*, Idempotency-Key e Problem Details (`backend/apps/tenancy/views.py`, `backend/apps/tenancy/urls.py`)
- [ ] T026 [US5] Reutilizar storage/serviço `seed_idempotency` no `/api/v1/seed-profiles/validate` (TTL 24h, dedupe, auditoria; replay determinístico) (`backend/apps/tenancy/services/seed_idempotency.py`, `backend/apps/tenancy/views.py`)

## Fase 4: User Story 1 - Seeds baseline multi-tenant (Prioridade P1)
Objetivo da história: Executar `seed_data --profile` para baseline deterministica por tenant/ambiente, bloqueando cross-tenant e falhando em falta de RLS/off-peak.  
Critério de teste independente: `seed_data` baseline roda em dry-run com manifesto v1 válido, respeita RLS, não grava WORM/checkpoints e devolve Problem Details auditável ao violar regras (incluindo falha OTEL/Sentry simulada).

### Testes (executar antes da implementacao)
- [ ] T027 [P] [US1] Cobrir comando `seed_data` baseline com dry-run (sem WORM/checkpoints), RLS/off-peak e idempotency_key (sucesso e bloqueios cross-tenant) (`backend/apps/tenancy/tests/test_seed_data_command.py`)
- [ ] T028 [P] [US1] Testes negativos de autorização (CLI/API) para perfis seed-runner/admin/read, janela off-peak e tenants/ambientes não permitidos (`backend/apps/tenancy/tests/test_seed_auth.py`)
- [ ] T029 [P] [US1] Bloquear runs quando `reference_datetime` divergir do checkpoint e exigir limpeza/reseed controlado (`backend/apps/tenancy/tests/test_seed_reference_datetime_drift.py`)

### Implementacao
- [ ] T030 [US1] Implementar SeedRunService para criar SeedRun/SeedBatch com advisory lock e store de idempotencia (baseline) (`backend/apps/tenancy/services/seed_runs.py`)
- [ ] T031 [US1] Criar management command `seed_data` baseline (carrega manifesto, preflight RLS, dry-run, checkpoints iniciais) (`backend/apps/tenancy/management/commands/seed_data.py`)
- [ ] T032 [US1] Atualizar quickstart com fluxo baseline, codigos de saida e exemplos de manifesto (`specs/003-seed-data-automation/quickstart.md`)
- [ ] T033 [US1] Configurar mocks/stubs Pact/Prism para integrações externas e validar bloqueio de chamadas reais (`contracts/pacts/*.json`, `scripts/ci/validate-seed-contracts.sh`)
- [ ] T034 [US1] Implementar limpeza/forçar reseed ao detectar drift de `reference_datetime` em manifesto e checkpoints (`backend/apps/tenancy/services/seed_runs.py`, `backend/apps/tenancy/management/commands/seed_data.py`)

## Fase 5: User Story 2 - Factories com PII mascarada (Prioridade P2)
Objetivo da história: Produzir factories factory-boy deterministicas com PII mascarada via Vault Transit, reutilizaveis em testes e contratos.  
Critério de teste independente: factories geram payloads mascarados que passam validacao de serializers/contratos e mantem determinismo por tenant/ambiente/manifesto.

### Testes (executar antes da implementacao)
- [ ] T035 [P] [US2] Validar determinismo/seed e mascaramento FPE das factories (PII nao vazada) (`backend/apps/banking/tests/test_factories_pii.py`)
- [ ] T036 [P] [US2] Validar factories contra serializers/contratos `/api/v1` (payloads validos e sem drift) (`backend/apps/banking/tests/test_factories_contracts.py`)

### Implementacao
- [ ] T037 [US2] Reusar helper único (`foundation/services/seed_utils.py`) na base de factories com seed deterministico e injeção de cliente Vault Transit (`backend/apps/banking/tests/factories.py`, `backend/apps/foundation/services/seed_utils.py`)
- [ ] T038 [US2] Implementar factories para entidades banking usando base/shared helpers e validacao via serializers (`backend/apps/banking/tests/factories.py`)
- [ ] T039 [US2] Implementar servico financeiro (CET/IOF/parcelas) e stub Pact para factories (`backend/apps/banking/services/financial_calculations.py`, `contracts/pacts/financial-calculator.json`)

## Fase 6: User Story 4 - Orquestrar seed runs via API/CLI (Prioridade P2)
Objetivo da história: Agendar, consultar e cancelar execuções via API/CLI com governança de RateLimit/Idempotency/ETag e rollback/flags conforme Art. VIII.  
Critério de teste independente: API/CLI `/seed-runs*` retornam headers obrigatórios, aplicam locks/rate-limit/budget e respeitam RBAC/ABAC (Problem Details previsíveis).

### Testes (executar antes da implementacao)
- [ ] T040 [P] [US4] Cobrir `/api/v1/seed-runs` create/get/cancel com Idempotency-Key, ETag/If-Match e RateLimit-* (`backend/apps/tenancy/tests/test_seed_runs_api.py`)
- [ ] T041 [P] [US4] Testes negativos de RBAC/ABAC para create/poll/cancel seed runs (perfis seed-runner/admin/read, If-Match/Idempotency-Key, tenants/ambientes proibidos) (`backend/apps/tenancy/tests/test_seed_runs_auth.py`)
- [ ] T042 [P] [US4] Validar armazenamento de `Idempotency-Key` com TTL/deduplicação (replay retorna resposta anterior, expiração configurável por modo) (`backend/apps/tenancy/tests/test_seed_idempotency.py`)
- [ ] T043 [P] [US4] Adicionar script/perf gate k6 para validate/create/poll seed runs lendo thresholds de SLO/rate_limit/budget do manifesto (`observabilidade/k6/seed-data-smoke.js`)

### Implementacao
- [ ] T044 [US4] Expor views/serializers `/api/v1/seed-runs` create/poll/cancel com RBAC/ABAC e headers governanca (RateLimit-*, Idempotency-Key, ETag) (`backend/apps/tenancy/views.py`, `backend/apps/tenancy/serializers/seed_runs.py`, `backend/apps/tenancy/urls.py`)
- [ ] T045 [US4] Ajustar `seed_data` e GC da fila para modos baseline/carga/DR (TTL, off-peak enforcement, cancelamento seguro) (`backend/apps/tenancy/management/commands/seed_data.py`, `backend/apps/tenancy/services/seed_queue_gc.py`)
- [ ] T046 [US4] Persistir `Idempotency-Key` com TTL/deduplicação auditável (tabela/cache) e limpeza periódica (`backend/apps/tenancy/services/seed_idempotency.py`, `backend/apps/tenancy/management/commands/seed_data.py`)

## Fase 7: User Story 3 - Carga e DR com dados sinteticos (Prioridade P3)
Objetivo da história: Executar modos carga/DR com caps Q11, rate limit/backoff, DLQ e evidencias WORM assinadas dentro de RPO/RTO.  
Critério de teste independente: CLI/API criam seed runs carga/DR respeitando RateLimit-*, produzem relatorio WORM assinado e cancelam/reagendam em 429/budget.

### Testes (executar antes da implementacao)
- [ ] T047 [P] [US3] Simular batches Celery com backoff/jitter, DLQ e retomada por checkpoint (429/erro transitorio) (`backend/apps/tenancy/tests/test_seed_batches.py`)
- [ ] T048 [P] [US3] k6 carga/DR exercitando geração de batches (caps Q11, rate-limit, throughput) com thresholds de p95/p99/erro e consumo de budget (`observabilidade/k6/seed-data-load.js`)
- [ ] T049 [P] [US3] Validar RPO≤5min/RTO≤60min em execuções carga/DR com manifesto canônico em staging (inclui janela off-peak e evidência WORM) (`backend/apps/tenancy/tests/test_seed_rpo_rto.py`)
- [ ] T050 [P] [US3] Gate de SLO/error budget em runtime abortando/reagendando runs quando p95/p99/throughput excedem manifesto (`backend/apps/tenancy/tests/test_seed_error_budget_gate.py`)

### Implementacao
- [ ] T051 [US3] Implementar tasks Celery de seeds com backoff+jitter, ordenacao de entidades e DLQ (`backend/apps/tenancy/tasks.py`, `backend/apps/tenancy/services/seed_batches.py`)
- [ ] T052 [US3] Integrar BudgetRateLimit/FinOps (caps, reset, abort em estouro) e retorno de RateLimit-* (`backend/apps/tenancy/services/budget.py`)
- [ ] T053 [US3] Gerar relatorio WORM assinado (hash/assinatura/verificacao) sem fallback (fail-closed se indisponível) e com verificação pós-upload (`backend/apps/tenancy/services/seed_worm.py`, `docs/runbooks/worm/seed-data.md`)
- [ ] T054 [US3] Incluir checklist automatizado PII/RLS/contratos/idempotencia/rate-limit/SLO no relatório WORM e garantir rotulagem/auditoria por execução/tenant (`backend/apps/tenancy/services/seed_worm.py`, `observabilidade/`, `.github/workflows/`)
- [ ] T055 [US3] Roteamento de outbox/CDC para sinks sandbox e testes de isolamento (sem side effects reais) (`backend/apps/tenancy/services/seed_batches.py`)
- [ ] T056 [US3] Guardrail anti-snapshot/dump de producao para seeds/factories (fail-closed no CI) (`scripts/ci/seed-guardrails.sh`)
- [ ] T057 [US3] Instrumentar flags/canary e métricas DORA para seed_data (rollback ensaiado) (`backend/apps/tenancy/feature_flags.py`, `docs/runbooks/observabilidade.md`)
- [ ] T058 [US3] Automatizar dependências de seeds/factories/Vault/perf com bloqueio de CVEs críticos (renovate, SCA) (`renovate.json`, `scripts/ci/deps-seed.sh`)
- [ ] T059 [US3] Gate GitOps/Argo CD: drift detection, janela off-peak e rollback validado para seed_data (`configs/seed_profiles/`, `.github/workflows/ci-*.yml`)
- [ ] T060 [US3] Gate de ambiente/off-peak: bloquear carga/DR fora de staging ou sem evidência WORM válida antes da promoção (`backend/apps/tenancy/services/seed_runs.py`, `.github/workflows/`, `configs/seed_profiles/`)
- [ ] T061 [US3] Integrar cost-model a BudgetRateLimit e relatório WORM (fail-close se ausente ou versão incompatível) (`backend/apps/tenancy/services/budget.py`, `backend/apps/tenancy/services/seed_worm.py`)
- [ ] T062 [US3] Implementar monitor/gate de SLO/error budget em runtime (p95/p99/throughput) abortando/reagendando runs e registrando Problem Details/relatório WORM (`backend/apps/tenancy/services/seed_observability.py`, `backend/apps/tenancy/services/seed_runs.py`)

## Fase Final: Polish & Cross-Cutting
Objetivo: Encerrar observabilidade/compliance e amarrar docs/runbooks.  
Critério de teste independente: pipelines com lint/tests/perf e docs gate verdes; observabilidade/seguranca ativas sem drift.

- [ ] T063 Consolidar spans/metricas/logs OTEL+Sentry/Grafana para seed_data (labels tenant/ambiente/run) (`observabilidade/`, `docs/runbooks/observabilidade.md`)
- [ ] T064 Atualizar docs/plan/ADRs e rodar `check-docs-needed` para feature (specs/plan/quickstart/runbooks) (`specs/003-seed-data-automation/plan.md`, `specs/003-seed-data-automation/spec.md`, `specs/003-seed-data-automation/quickstart.md`, `scripts/ci/check-docs-needed.js`)
- [ ] T065 Publicar threat model STRIDE/LINDDUN, runbook e GameDay seeds/carga/DR com critérios de sucesso (`docs/runbooks/seed-data.md`)
- [ ] T066 Garantir gates de CI (cobertura ≥85%, cc≤10, SAST/DAST/SCA/SBOM, k6 alinhado a SLOs) ativos para a feature (`.github/workflows/`, `docs/pipelines/ci-required-checks.md`)
- [ ] T067 Gate de observabilidade fail-close: simular falha de export/redaction OTEL/Sentry e bloquear pipeline/execução (`observabilidade/`, `docs/runbooks/observabilidade.md`, `.github/workflows/`)
- [ ] T068 Gate Trunk-Based/rollback no CI/Argo (branches curtas, squash-only, histórico linear, rollback ensaiado) com bloqueio de promoção quando violado (`.github/workflows/`, `docs/pipelines/ci-required-checks.md`)
- [ ] T069 Checklist anti-poluição: reprovar se logs/WORM faltarem labels obrigatórios ou conterem PII, com validação automática no CI/Argo (`backend/apps/tenancy/services/seed_worm.py`, `scripts/ci/check-audit-cleanliness.sh`)

## Dependencias e ordem de historias
- Fundacional (T006–T020) precede qualquer história; Setup (T001–T005) pode avançar em paralelo a Fundacional. Convergência obrigatória: preflight Vault/WORM (T016) e cap global/TTL fila (T012–T013) antes de validar/rodar baseline.
- US5 (validação de manifestos) → US1 (baseline) → US2 (factories) → US4 (API/CLI seed-runs) → US3 (carga/DR). US5 exige schema/manifesto Q11 (T023) e idempotência do validate (T022/T026) antes de expor baseline. US1 requer locks/idempotência (T030), drift cleanup (T029/T034) e stubs (T033).
- US4 depende de Fundacional + contratos prontos; Idempotency TTL/ETag/RateLimit são fechados em T040–T046 antes de execuções remotas. US3 herda serviços/API/CLI prontos e precisa dos testes T047–T050 antes de T051–T062 (TDD). Polish depende de todas as fases.

## Paralelizacao sugerida
- Setup: T001–T005 em paralelo (contratos, manifestos, CI alvo).
- Fundacional: T006–T011 em paralelo; T012/T013 após filas; T016 cedo para preflight; T017–T020 em paralelo com migrations concluídas.
- US5: T021–T022 em paralelo; T023–T026 em ordem (schema → validador → endpoint → idempotência).
- US1: T027–T029 em paralelo após Fundacional; T030–T031–T032–T033–T034 em ordem (serviço → comando → quickstart → stubs → cleanup).
- US2: T035/T036 em paralelo após helpers; T037–T039 após serializers/helpers prontos.
- US4: T040–T043 em paralelo após Fundacional; T044–T046 em ordem (API → GC → idempotência persistida).
- US3: T047–T050 primeiro (TDD), em paralelo após Fundacional e contratos; implementações T051–T062 seguem os testes, com FinOps/WORM/observabilidade avançando em paralelo respeitando dependências.
- Polish: T063–T069 após histórias concluídas.

## Estrategia de implementacao (MVP primeiro)
1) Entregar MVP com Setup + Fundacional + US5 (validação de manifestos) + US1 (baseline CLI/API) incluindo preflight Vault/WORM, cap global/TTL da fila, schema/manifesto Q11, idempotência, drift cleanup e quickstart atualizado.  
2) Expandir com US2 (factories mascaradas determinísticas e serviço financeiro + Pact).  
3) Entregar US4 (API/CLI seed-runs com RateLimit/Idempotency/ETag e k6 smoke).  
4) Entregar US3 (carga/DR: Celery/DLQ, FinOps/RateLimit, WORM, perf gates k6, RPO/RTO, SLO/error budget runtime).  
5) Finalizar com Polish (observabilidade fail-close, docs/ADRs, threat model/GameDay, CI gates, checklist anti-poluição).

## Validação de completude
Todas as user stories possuem testes dedicados (contrato/CLI/factories/API/CLI/Celery/perf), tarefas de implementacao e paths claros. Gates adicionais incluídos: preflight Vault/WORM (T016), SLO/SLI/error budget (T017/T050/T062), cap global/TTL fila (T012–T013), IaC/OPA/Argo (T018), expand/contract (T019), stubs externos (T033), checklist WORM e rotulagem/auditoria (T054/T069), outbox/CDC sandbox (T055), guardrail anti-snapshot (T056), flags/canary/DORA (T057), dependências/SCA (T058), drift/off-peak/GitOps (T059–T060), cost-model FinOps (T020/T061), perf gate carga/DR (T048), RPO/RTO (T049), fail-close observabilidade (T067), drift `reference_datetime`/cleanup (T029/T034), dedupe/TTL de Idempotency-Key (T022/T026/T042/T046), k6 lendo thresholds do manifesto (T043/T048) e gate Trunk-Based/rollback (T068). Dry-run sem WORM/checkpoints e com falha OTEL/Sentry simulada está coberto em T003/T027.
