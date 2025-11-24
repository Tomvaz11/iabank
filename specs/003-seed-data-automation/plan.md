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
**Observabilidade**: OTEL com W3C Trace Context, structlog/django-prometheus/Sentry (ADR-012); traces/metricas/logs etiquetados por tenant/ambiente/execucao; redacao de PII obrigatoria; export falho bloqueia.  
**Segurança/Compliance**: RBAC/ABAC minimo para `seed_data`, RLS enforced, mascaramento PII deterministico (Vault Transit FPE), FinOps budgets/caps por manifesto, evidencias WORM assinadas, mocks para integrações externas (OWASP/NIST; Art. XII, XIII, XVI).  
**Performance Targets**: p95/p99 de execucao por manifesto dentro do budget; throughput alinhado a RateLimit-* e idempotencia; DR cumpre RPO≤5 min/RTO≤60 min; error budget consumido/abortado conforme manifesto.  
**Restrições Operacionais**: TDD/integ-primeiro, execucao apenas em janela off-peak declarada, bloqueio sem RLS ou drift de manifesto, RLS check preflight, somente dados sinteticos, GitOps/Argo CD com flags/canary/rollback; expand/contract para schema.  
**Escopo/Impacto**: Tenants/ambientes multi-tenant, modos baseline/carga/DR, APIs `/api/v1` consumidas/testadas, pipelines CI/CD, infra de Vault/WORM/filas/Terraform; sem dependencias externas reais (stubs Pact).

## Constitution Check

*GATE: Validar antes da Fase 0 e reconfirmar apos o desenho de Fase 1.*

- [x] **Art. III - TDD**: Suites pytest/pytest-django planejadas para `seed_data` (baseline/carga/DR), factories com mascaramento e checagens de idempotencia/rate-limit; iniciar em `/home/pizzaplanet/meus_projetos/iabank/backend/apps/**/tests/` com falha antes de codigo.  
- [x] **Art. VIII - Lancamento Seguro**: Flags/canary por ambiente/tenant, rollback via Argo CD, budget de erro por manifesto e relatorio WORM vinculado; documentado neste plano e quickstart.  
- [x] **Art. IX - Pipeline CI**: Cobertura≥85%, complexidade≤10, SAST/DAST/SCA/SBOM, k6 perf gate e dry-run deterministico mapeados; falha bloqueia promocao (ver spec/quickstart).  
- [x] **Art. XI - Governanca de API**: Contratos OpenAPI 3.1 em `/home/pizzaplanet/meus_projetos/iabank/specs/003-seed-data-automation/contracts/seed-data.openapi.yaml` e alinhamento a `contracts/api.yaml`; lint/diff/Pact previstos e versionamento SemVer.  
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

- **Contrato**: `/api/v1/seed-profiles/validate` ja descrito em `specs/003-seed-data-automation/contracts/seed-data.openapi.yaml` (OpenAPI 3.1, Problem Details, RateLimit-*, Idempotency-Key).  
- **Handler**: `backend/apps/tenancy/views.py:SeedProfileValidateView` registrado em `backend/apps/tenancy/urls.py` sob `path("api/v1/seed-profiles/validate", ...)`, respeitando middleware de RLS/tenant e ABAC.  
- **Regras**: Valida schema v1 do manifesto (JSON Schema 2020-12) incluindo `mode` (baseline/carga/dr), `reference_datetime` ISO 8601 UTC, janela off-peak `start_utc/end_utc` (única, pode cruzar meia-noite), caps Q11 por entidade, rate limit/backoff+jitter, budget/TTL e `salt_version`. Falha fail-closed em: versão incompatível, drift de campos obrigatórios, janela fora do formato ou caps ausentes.  
- **Respostas**: `200` com `valid=true`, `issues=[]`, `normalized_version` e `caps` extraídos; `422` Problem Details com lista de issues; `429` aplica backoff curto; `401/403` em ausência de autorização/RLS. Sempre retorna `RateLimit-*`, `Retry-After` e exige `Idempotency-Key`.  
- **Observabilidade**: OTEL + Sentry com labels `tenant_id`, `environment`, `manifest_version`, `reference_datetime`, marcando chamadas inválidas como `error` e emitindo métricas de taxa de rejeição (Art. VII/ADR-012).  
- **Stubs/Tests**: Stubs Pact/Prism gerados do contrato; teste de integração em `backend/apps/tenancy/tests/test_seed_profile_validate_api.py` cobre happy path e 422, incluindo headers obrigatórios e Problem Details.

### Fluxo operacional do comando `seed_data`

- **Preflight**: Checar migrations pendentes; validar enforcement de RLS (Art. XIII), flags/canary do domínio e disponibilidade do Vault/WORM; abortar fail-closed se qualquer pré-condição falhar.  
- **Validação de manifesto**: Carregar manifesto YAML/JSON (GitOps) e validar contra JSON Schema v1 (JSON Schema 2020-12). Campos obrigatórios: `metadata` (tenant, ambiente, profile/version, salt_version), `mode` (baseline/carga/dr), `reference_datetime` ISO 8601 UTC, `window.start_utc/end_utc` (única, pode cruzar meia-noite), `volumetry` por entidade (caps Q11), `rate_limit` (limit/window) + `backoff` (base/jitter/max_retries), `budget` (cost/error budget), `ttl` por modo, `slo` (p95/p99 alvo), `caps_override` opcional para dev. Versão divergente ou ausência de campos → fail-closed.  
- **Concorrência/locks**: Adquirir lock global (teto 2 execuções por ambiente/cluster, TTL fila 5 min) e lock por tenant/ambiente via advisory lock (TTL 60s) no Postgres; fila curta auditável no DB; liberação em finally; se lock expirar, reagendar.  
- **Criação de SeedRun/SeedBatch**: Persistir `SeedRun` com `idempotency_key`, status `queued` e manifesto referenciado; para cada entidade/caps gerar `SeedBatch` inicial com attempt=0 e status `pending`.  
- **Execução (Celery/Redis)**: Disparar lotes Celery com `acks_late`, backoff com jitter em 429/erro transitório, DLQ com teto de tentativas definido no manifesto; baseline sequencial, carga/DR com paralelismo controlado (2–4 workers) respeitando rate limit centralizado.  
- **Checkpoints/idempotência**: Cada lote grava `Checkpoint` (hash_estado, resume_token criptografado via pgcrypto) e atualiza `SeedRun`/`BudgetRateLimit`; divergência de hash ou checkpoint vencido → abort e exigir limpeza/reseed. TTL de checkpoint até próximo reseed do modo, máx. 30 dias.  
- **Observabilidade**: OTEL (traces/metrics/logs JSON) com labels tenant/ambiente/seed_run_id/manifest_version; redaction PII (ADR-010); spans de lote e de validação de manifesto; erro no export marca run como failed.  
- **Relatório WORM**: Ao final (ou falha), gerar relatório JSON assinado (hash/assinatura) com manifest/tenant/ambiente, trace/span IDs, volumetria prevista/real, uso de rate limit/budget, SLO atingidos, erros Problem Details; armazenar em WORM (ex.: S3 Object Lock) com retenção mínima 1 ano e integridade verificada; indisponibilidade de WORM → abort antes de escrever dados.  
- **Limpeza/expurgo**: Modos carga/DR limpam dataset do modo antes de recriar; TTL de datasets de carga/DR executado via Argo CronJob; dry-run não persiste checkpoints nem WORM.

### Manifesto `seed_profile` — schema v1

- **Fonte**: Manifestos versionados em `configs/seed_profiles/<ambiente>/<tenant>.yaml` (GitOps/Argo CD). JSON Schema v1 a publicar em `specs/003-seed-data-automation/contracts/seed-profile.schema.json` (JSON Schema 2020-12) e usado pelo endpoint `/api/v1/seed-profiles/validate`.  
- **Campos obrigatórios**:  
  - `metadata`: `tenant`, `environment`, `profile`, `version` (SemVer), `schema_version`, `salt_version`, `reference_datetime` (ISO 8601 UTC).  
  - `mode`: `baseline|carga|dr`; `window.start_utc/end_utc` (par único, UTC, pode cruzar meia-noite).  
  - `volumetry`: caps Q11 por entidade; `rate_limit` (`limit`, `window_seconds`), `backoff` (`base_seconds`, `jitter`, `max_retries`), `budget` (`cost_cap`, `error_budget`), `ttl` por modo.  
  - `slo`: `p95_target_ms`, `p99_target_ms`, `throughput_target`.  
  - `canary`: escopo obrigatório para modo canary (percentual ou tenants-alvo).  
- **Regras**: Versão nova de `reference_datetime` é breaking e exige reseed/limpeza de checkpoints; schema_version divergente → fail-closed; overrides só permitidos em dev isolado.  
- **Evidência**: Manifesto e hash de integridade referenciados no relatório WORM e no `SeedRun.profile_version`.

### Alinhamento CLI x API

- **CLI (`manage.py seed_data`)**: Caminho primário para execuções controladas (CI/PR dry-run, staging carga/DR). Orquestra locks, criação de `SeedRun/SeedBatch`, chamadas Celery e relatório WORM.  
- **API `/api/v1/seed-runs*`**: Usada para agendar/cancelar/consultar execuções de forma remota (Argo/CD/portais internos); retorna RateLimit-*, Idempotency-Key e ETag/If-Match; reutiliza mesma camada de serviço da CLI.  
- **Contrato/serviço único**: Serviços de aplicação em `backend/apps/tenancy/services/seed_runs.py` (a criar) expostos tanto via CLI quanto via API para evitar divergência; checkpoints/idempotência persistidos sempre no banco com RLS.

### Observabilidade, FinOps e rate limit

- **Rate limit/FinOps**: Manifesto define caps; calcular consumo e alertar em 80% do budget; abort/rollback em 100% (fail-closed). Propagar cabeçalhos `RateLimit-*`/`Retry-After` em API e logs de CLI; registrar consumo no relatório WORM.  
- **SLO**: Medir p95/p99 de execução por manifesto e throughput por lote; violação consome error budget e pode abortar.  
- **Telemetria**: Conformidade com ADR-012 (OTEL + Sentry) e ADR-010 (redação PII). Falha de export → marca SeedRun como failed e bloqueia promoção (Art. VII).  
- **PII**: FPE determinística via Vault Transit (FF3-1/FF1), chaves/salts por ambiente/tenant com rotação trimestral; fallback apenas em dev isolado; pgcrypto em repouso; catálogo PII aplicado nas factories.

### Cobertura de entidades e factories

- **Escopo mínimo**: tenants/usuários, clientes/endereços, consultores, contas bancárias/categorias/fornecedores, empréstimos/parcelas, transações financeiras, limites/contratos (conforme clarificações).  
- **Factories**: factory-boy determinísticas (seed derivado de tenant/ambiente/manifesto), mascaramento PII obrigatório, compatíveis com serializers `/api/v1`; validam CET/IOF/parcelas contra serviços oficiais.  
- **Baseline vs carga/DR**: Baseline somente happy paths/estados ativos; carga/DR incluem estados bloqueado/inadimplente/cancelado com percentuais por entidade no manifesto; reexecução limpa datasets do modo antes de recriar.

## Complexity Tracking

*Preencha somente quando algum item da Constitution Check estiver marcado como N/A/violado. Cada linha deve citar explicitamente o artigo impactado e o ADR/clarify que respalda a excecao.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| | | |
