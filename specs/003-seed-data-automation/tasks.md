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
Critério de teste independente: contratos e manifestos canônicos passam lint/diff e podem ser usados pelo comando `seed_data` em modo dry-run.

- [ ] T001 Publicar contratos seed-data e schema para lint/diff (`contracts/seed-data.openapi.yaml`, `contracts/seed-profile.schema.json`)
- [ ] T002 Criar manifestos canônicos baseline/carga/DR para testes/dry-run (`configs/seed_profiles/staging/tenant-a.yaml`, `configs/seed_profiles/dr/tenant-a.yaml`)
- [ ] T003 Adicionar alvo CI/Makefile para `seed_data` validate/dry-run com idempotency key (`Makefile`, `scripts/ci/seed-data.sh`)

## Fase 2: Fundacional (bloqueios compartilhados)
Objetivo: Estruturar apps, modelos, politicas RLS/ABAC, utils de determinismo/PII e filas Celery/contract lint.  
Critério de teste independente: migrations e politicas passam testes de modelo/RLS e lint de contratos seed-data roda no CI.

- [ ] T004 Criar e registrar app `banking` nas settings do Django (`backend/apps/banking/apps.py`, `backend/config/settings.py`)
- [ ] T005 Modelar/migrar entidades bancarias com managers RLS (Customer, Address, Consultant, BankAccount, AccountCategory, Supplier, Loan, Installment, FinancialTransaction, CreditLimit, Contract) (`backend/apps/banking/models/*.py`, `backend/apps/banking/migrations/0001_initial.py`)
- [ ] T006 Modelar/migrar tabelas de seeds e auditoria (SeedProfile, SeedRun, SeedBatch, Checkpoint, SeedQueue, SeedDataset, SeedIdempotency, SeedRBAC, BudgetRateLimit, EvidenceWORM) (`backend/apps/tenancy/models/seed_*.py`, `backend/apps/tenancy/migrations/`)
- [ ] T007 Adicionar politicas RLS/ABAC e managers para novas tabelas de seeds (`backend/apps/tenancy/sql/rls_policies.sql`, `backend/apps/tenancy/managers.py`)
- [ ] T008 Implementar helpers de determinismo/idempotencia e cliente Vault Transit FPE reutilizavel (`backend/apps/foundation/services/seed_utils.py`)
- [ ] T009 Configurar filas Celery/Redis (default, load_dr, dlq) e roteamento para seed_data com acks tardios (`backend/config/settings.py`, `backend/apps/tenancy/tasks.py`, `backend/celery.py`)
- [ ] T010 Configurar lint/diff de contratos seed-data e JSON Schema no CI (Spectral/oasdiff) (`scripts/ci/validate-seed-contracts.sh`, `package.json`)
- [ ] T011 Criar testes basicos de migracoes/RLS para tabelas banking e seeds (`backend/apps/banking/tests/test_models.py`, `backend/apps/tenancy/tests/test_seed_models.py`)
- [ ] T034 Publicar SLO/SLI/error budget para seed_data e alinhar thresholds do k6 (docs/slo/seed-data.md, observabilidade/k6/seed-data-smoke.js)
- [ ] T035 Terraform/OPA para Vault/WORM/filas e pipeline Argo CD com drift/rollback e janela off-peak (`infra/`, `scripts/ci/validate-opa.sh`)
- [ ] T036 Garantir migrações expand/contract com índices CONCURRENTLY e testes de rollback (`backend/apps/**/migrations/`, `scripts/ci/check-migrations.sh`)

## Fase 3: User Story 1 - Seeds baseline multi-tenant (Prioridade P1)
Objetivo da história: Executar `seed_data --profile` para baseline deterministica por tenant/ambiente, bloqueando cross-tenant e falhando em falta de RLS/off-peak.  
Critério de teste independente: baseline roda em dry-run com manifesto v1 valido, respeita RLS e devolve Problem Details auditavel ao violar regras.

### Testes (executar antes da implementacao)
- [ ] T012 [P] [US1] Cobrir 200/422/429 do endpoint `/api/v1/seed-profiles/validate` com headers obrigatorios e Problem Details (`backend/apps/tenancy/tests/test_seed_profile_validate_api.py`)
- [ ] T013 [P] [US1] Cobrir comando `seed_data` baseline com dry-run, RLS/off-peak e idempotency_key (sucesso e bloqueios cross-tenant) (`backend/apps/tenancy/tests/test_seed_data_command.py`)

### Implementacao
- [ ] T014 [US1] Implementar validador JSON Schema v1 + preflight de manifesto (versao/schema/hash/off-peak) (`backend/apps/tenancy/services/seed_manifest_validator.py`)
- [ ] T015 [US1] Expor `/api/v1/seed-profiles/validate` com RateLimit-*, Idempotency-Key e Problem Details (`backend/apps/tenancy/views.py`, `backend/apps/tenancy/urls.py`)
- [ ] T016 [US1] Implementar SeedRunService para criar SeedRun/SeedBatch com advisory lock e store de idempotencia (`backend/apps/tenancy/services/seed_runs.py`)
- [ ] T017 [US1] Criar management command `seed_data` baseline (carrega manifesto, preflight RLS, dry-run, checkpoints iniciais) (`backend/apps/tenancy/management/commands/seed_data.py`)
- [ ] T018 [US1] Atualizar quickstart com fluxo baseline, codigos de saida e exemplos de manifesto (`specs/003-seed-data-automation/quickstart.md`)
- [ ] T037 [US1] Configurar mocks/stubs Pact/Prism para integrações externas e validar bloqueio de chamadas reais (`contracts/pacts/*.json`, `scripts/ci/validate-seed-contracts.sh`)

## Fase 4: User Story 2 - Factories com PII mascarada (Prioridade P2)
Objetivo da história: Produzir factories factory-boy deterministicas com PII mascarada via Vault Transit, reutilizaveis em testes e contratos.  
Critério de teste independente: factories geram payloads mascarados que passam validacao de serializers/contratos e mantem determinismo por tenant/ambiente/manifesto.

### Testes (executar antes da implementacao)
- [ ] T019 [P] [US2] Validar determinismo/seed e mascaramento FPE das factories (PII nao vazada) (`backend/apps/banking/tests/test_factories_pii.py`)
- [ ] T020 [P] [US2] Validar factories contra serializers/contratos `/api/v1` (payloads validos e sem drift) (`backend/apps/banking/tests/test_factories_contracts.py`)

### Implementacao
- [ ] T021 [US2] Criar base de factories com seed deterministico e injeção de cliente Vault Transit (`backend/apps/foundation/factory_utils.py`)
- [ ] T022 [US2] Implementar factories para entidades banking usando base/shared helpers e validacao via serializers (`backend/apps/banking/tests/factories.py`)
- [ ] T023 [US2] Implementar servico financeiro (CET/IOF/parcelas) e stub Pact para factories (`backend/apps/banking/services/financial_calculations.py`, `contracts/pacts/financial-calculator.json`)

## Fase 5: User Story 3 - Carga e DR com dados sinteticos (Prioridade P3)
Objetivo da história: Executar modos carga/DR com caps Q11, rate limit/backoff, DLQ e evidencias WORM assinadas dentro de RPO/RTO.  
Critério de teste independente: API/CLI criam seed runs carga/DR respeitando RateLimit-*, produzem relatorio WORM assinado e cancelam/reagendam em 429/budget.

### Testes (executar antes da implementacao)
- [ ] T024 [P] [US3] Cobrir `/api/v1/seed-runs` create/get/cancel com Idempotency-Key, ETag/If-Match e RateLimit-* (`backend/apps/tenancy/tests/test_seed_runs_api.py`)
- [ ] T025 [P] [US3] Simular batches Celery com backoff/jitter, DLQ e retomada por checkpoint (429/erro transitorio) (`backend/apps/tenancy/tests/test_seed_batches.py`)
- [ ] T026 [P] [US3] Adicionar script/perf gate k6 para validate/create/poll seed runs com thresholds (p95/p99/erro) (`observabilidade/k6/seed-data-smoke.js`)

### Implementacao
- [ ] T027 [US3] Expor views/serializers `/api/v1/seed-runs` create/poll/cancel com RBAC/ABAC e headers governanca (RateLimit-*, Idempotency-Key, ETag) (`backend/apps/tenancy/views.py`, `backend/apps/tenancy/serializers/seed_runs.py`, `backend/apps/tenancy/urls.py`)
- [ ] T028 [US3] Implementar tasks Celery de seeds com backoff+jitter, ordenacao de entidades e DLQ (`backend/apps/tenancy/tasks.py`, `backend/apps/tenancy/services/seed_batches.py`)
- [ ] T029 [US3] Integrar BudgetRateLimit/FinOps (caps, reset, abort em estouro) e retorno de RateLimit-* (`backend/apps/tenancy/services/budget.py`)
- [ ] T030 [US3] Gerar relatorio WORM assinado (hash/assinatura/verificacao) com fallback dev e integracao S3/Vault (`backend/apps/tenancy/services/seed_worm.py`, `docs/runbooks/worm/seed-data.md`)
- [ ] T031 [US3] Ajustar `seed_data` e GC da fila para modos carga/DR (TTL, off-peak enforcement, cancelamento seguro) (`backend/apps/tenancy/management/commands/seed_data.py`, `backend/apps/tenancy/services/seed_queue_gc.py`)
- [ ] T038 [US3] Incluir checklist automatizado PII/RLS/contratos/idempotencia/rate-limit/SLO no relatório WORM e bloquear promoções em reprovação (`backend/apps/tenancy/services/seed_worm.py`)
- [ ] T039 [US3] Roteamento de outbox/CDC para sinks sandbox e testes de isolamento (sem side effects reais) (`backend/apps/tenancy/services/seed_batches.py`)
- [ ] T040 [US3] Guardrail anti-snapshot/dump de producao para seeds/factories (fail-closed no CI) (`scripts/ci/seed-guardrails.sh`)
- [ ] T041 [US3] Instrumentar flags/canary e métricas DORA para seed_data (rollback ensaiado) (`backend/apps/tenancy/feature_flags.py`, `docs/runbooks/observabilidade.md`)
- [ ] T042 [US3] Automatizar dependências de seeds/factories/Vault/perf com bloqueio de CVEs críticos (renovate, SCA) (`renovate.json`, `scripts/ci/deps-seed.sh`)
- [ ] T043 [US3] Gate GitOps/Argo CD: drift detection, janela off-peak e rollback validado para seed_data (`configs/seed_profiles/`, `.github/workflows/ci-*.yml`)

## Fase Final: Polish & Cross-Cutting
Objetivo: Encerrar observabilidade/compliance e amarrar docs/runbooks.  
Critério de teste independente: pipelines com lint/tests/perf e docs gate verdes; observabilidade/seguranca ativas sem drift.

- [ ] T032 Consolidar spans/metricas/logs OTEL+Sentry/Grafana para seed_data (labels tenant/ambiente/run) (`observabilidade/`, `docs/runbooks/observabilidade.md`)
- [ ] T033 Atualizar docs/plan/ADRs e rodar `check-docs-needed` para feature (specs/plan/quickstart/runbooks) (`specs/003-seed-data-automation/plan.md`, `specs/003-seed-data-automation/spec.md`, `specs/003-seed-data-automation/quickstart.md`, `scripts/ci/check-docs-needed.js`)
- [ ] T044 Publicar threat model STRIDE/LINDDUN, runbook e GameDay seeds/carga/DR com critérios de sucesso (docs/runbooks/seed-data.md)
- [ ] T045 Garantir gates de CI (cobertura ≥85%, cc≤10, SAST/DAST/SCA/SBOM, k6 alinhado a SLOs) ativos para a feature (`.github/workflows/`, `docs/pipelines/ci-required-checks.md`)

## Dependencias e ordem de historias
- Fundacional (T004–T011) + guardrails base (T034–T036) precedem US1.
- US1 (baseline) → US2 (factories) → US3 (carga/DR). Foundacional completa antes de US1; US3 depende também de T037 (stubs externos) e dos gates T038–T043.
- Fase Final depende das histórias completas e dos gates/documentação.

## Paralelizacao sugerida
- Fundacional: T004–T011 em paralelo com T034–T036 (SLO/SLI, Terraform/OPA/Argo, expand/contract) após definição de modelos.
- US1: T012/T013 em paralelo após migrations; T014–T017 em ordem; T037 pode seguir após T010 (stubs/contratos prontos).
- US2: T019/T020 em paralelo após helpers (T021); T022/T023 em paralelo com T020 se serializers fechados.
- US3: T024–T026 em paralelo após T009/T010; T027 com T028 pode rodar em paralelo a T029/T030 quando contratos fechados; gates T038–T043 alinham antes de finalizar US3.

## Estrategia de implementacao (MVP primeiro)
1) Entregar MVP com Fase 1 + Fundacional + guardrails SLO/SLI + expand/contract (T034–T036) + US1 (baseline CLI/API validate) para habilitar dry-run determinístico.  
2) Expandir com US2 adicionando factories mascaradas para suportar testes/contratos e reutilizar no comando.  
3) Finalizar com US3 para modos carga/DR, perf gate, WORM, checklist WORM (T038) e guardrails (T039–T043).  
4) Encerrar com Polish para observabilidade, docs e governance.

## Validação de completude
Todas as user stories possuem testes dedicados (contrato/CLI/factories/Celery/perf), tarefas de implementacao e paths claros. Novos gates: SLO/SLI/error budget (T034), IaC/OPA/Argo (T035), expand/contract (T036), stubs externos (T037), checklist WORM (T038), outbox/CDC sandbox (T039), guardrail anti-snapshot (T040), flags/canary/DORA (T041), dependências/SCA (T042), drift/off-peak GitOps (T043). Cada fase entrega incremento testavel e independente, cobrindo contratos, RLS/ABAC, PII, FinOps, WORM e governança conforme spec/plan.
