# Data Model — F-11 Automacao de Seeds e Dados de Teste

## Overview

O foco desta feature é padronizar seeds e geração de dados de teste multi-tenant no monolito Django/DRF sobre PostgreSQL, garantindo anonimização forte de PII/PD, reexecução idempotente (incluindo cenários de DR) e integração com CI/CD, testes de contrato e de carga.  
As entidades abaixo cobrem principalmente:
- Metadados de execução de seeds e datasets (para auditoria, idempotência e FinOps).  
- Configurações declarativas de volumetria por ambiente/tenant.  
- Mapeamento de PII e regras de anonimização alinhadas à LGPD.  
O modelo respeita Art. I, III, IV, VII, IX, XI, XIII da Constituição e as diretrizes de `BLUEPRINT_ARQUITETURAL.md §§3.1, 6, 26`.

---

## Entities

> Entidades de domínio de negócio existentes (ex.: `Tenant`, `Customer`, `Loan`, `Transaction`, `User`) são referenciadas, mas não redescritas aqui; a ênfase está nas estruturas específicas de seeds/datasets.

### SeedProfile (config declarativa)
- **Descrição**: Representa um perfil declarativo de volumetria de seeds, versionado em YAML, combinando ambiente (`dev`, `hom`, `perf`, `dr`) e volume (`small`, `medium`, `large`) por entidade/tenant.
- **Tipo**: Configuração de arquivo (não persistido em tabela própria; carregado de `backend/apps/foundation/seeds/config/**.yaml`).
- **Campos (YAML)**:
  - `id` (string) — identificador lógico (`dev-small`, `perf-large`, etc.).
  - `environment` (enum: `dev`, `hom`, `perf`, `dr`, `review`).
  - `volume_profile` (enum: `small`, `medium`, `large`).
  - `entities` (mapa `entity_name -> EntityVolumeConfig`).
    - `EntityVolumeConfig.target_per_tenant` (integer) — número alvo de registros por tenant.
    - `EntityVolumeConfig.max_per_tenant` (integer, opcional) — teto por tenant (proteção FinOps).
    - `EntityVolumeConfig.enabled` (boolean) — permitir desativar entidades por perfil.
  - `max_duration_seconds` (integer, opcional) — limite esperado de duração do seed para o perfil.
- **Relações**:
  - Relacionado a `SeedRun.profile_id`.
- **Validações**:
  - `environment` e `volume_profile` devem ser combinados em um `id` único no conjunto de configs.
  - `target_per_tenant` deve respeitar faixas Q11 (por exemplo, dev/hom ≈50/200/500; perf ≈5000/20000/50000).
- **Regras**:
  - Perfis são imutáveis após usados em produção/DR; novas mudanças exigem novo `id`.
  - Pipelines de CI/CD selecionam perfis por `environment` + `volume_profile`.

---

### SeedRun
- **Descrição**: Registro de cada execução do comando `seed_data`, usado para auditoria, idempotência, DR e correlação com métricas de observabilidade.
- **Campos**:
  - `id` (UUID, PK).
  - `environment` (enum: `dev`, `hom`, `perf`, `dr`, `review`).
  - `profile_id` (string) — referência lógica ao `SeedProfile.id` usado.
  - `tenant_scope` (enum: `single`, `multi`, `all`) — escopo da execução.
  - `trigger_type` (enum: `ci_pipeline`, `infra_provision`, `manual`, `dr_restore`) — como a execução foi disparada.
  - `dry_run` (boolean) — indica execução apenas de análise, sem persistência final.
  - `status` (enum: `pending`, `running`, `success`, `failed`, `rolled_back`, `skipped`) — estado agregado da execução.
  - `started_at` / `finished_at` (timestamp with time zone).
  - `duration_ms` (integer, derivado).
  - `trace_id` (string) — ID de trace OpenTelemetry (W3C Trace Context).
  - `initiated_by` (string, opcional) — identificador do pipeline/usuário (ex.: `github-actions`, `argo-job`, `platform-team`).
  - `error_summary` (text, opcional) — síntese de erros, sem PII.
- **Relações**:
  - 1:N com `SeedRunEntityMetric`.
  - 1:N com `SeedDatasetSnapshot`.
- **Validações**:
  - `finished_at` obrigatório quando `status ∈ {success, failed, rolled_back, skipped}`.
  - `duration_ms` ≥ 0.
- **Regras**:
  - Deve ser criado no início do `seed_data` e atualizado ao final, dentro de transação ou com garantias de idempotência para não poluir o histórico em caso de reexecuções.
  - IDs de `SeedRun` devem ser referenciáveis em logs/traces para auditoria.
- **Implementação**:
  - Novo modelo em `backend/apps/foundation/models/seed_run.py`.
  - Managers em `backend/apps/foundation/managers.py` para consultas filtradas por ambiente/status.
  - Migrações em `backend/apps/foundation/migrations/` com RLS baseada em `environment`/tenant, se aplicável ao modelo de auditoria.

---

### SeedRunEntityMetric
- **Descrição**: Métricas por entidade/tenant dentro de uma execução de seeds, usadas para relatórios e verificação de idempotência.
- **Campos**:
  - `id` (UUID, PK).
  - `seed_run_id` (UUID, FK → SeedRun.id).
  - `tenant_id` (UUID, FK → Tenant.id) — respeita RLS multi-tenant.
  - `entity_name` (string, ex.: `Customer`, `Loan`, `Transaction`, `User`).
  - `target_count` (integer) — número objetivo de registros para a entidade/tenant.
  - `existing_count` (integer) — registros encontrados antes da execução.
  - `created_count` (integer) — registros novos criados.
  - `reused_count` (integer) — registros reaproveitados (nenhuma duplicação).
  - `updated_count` (integer) — registros atualizados.
  - `error_count` (integer) — falhas ao criar/atualizar.
  - `duration_ms` (integer) — tempo gasto na entidade/tenant.
  - `pii_scan_status` (enum: `not_applicable`, `pending`, `pass`, `fail`) — resultado da verificação de PII quando aplicável.
- **Relações**:
  - N:1 com `SeedRun`.
  - N:1 com `Tenant`.
- **Validações**:
  - Todos os contadores ≥ 0.
  - `target_count >= created_count + reused_count`.
- **Regras**:
  - Em caso de falha de consistência, `SeedRun.status` deve ser marcado como `failed` e a pipeline deve falhar explicitamente.  
  - Campos agregados podem alimentar métricas Prometheus (por ambiente/tenant/entidade).
- **Implementação**:
  - Novo modelo em `backend/apps/foundation/models/seed_run_entity_metric.py`.
  - RLS garantindo que consultas em contexto de tenant só acessem métricas do tenant corrente (Art. XIII).

---

### SeedDatasetSnapshot
- **Descrição**: Metadados sobre datasets gerados a partir de uma execução de seeds para uso em testes funcionais, de contrato e de carga.
- **Campos**:
  - `id` (UUID, PK).
  - `seed_run_id` (UUID, FK → SeedRun.id).
  - `environment` (enum: `dev`, `hom`, `perf`, `dr`, `review`).
  - `profile_id` (string) — copia o `SeedProfile.id` associado.
  - `tenant_id` (UUID, FK → Tenant.id, opcional) — datasets podem ser multi-tenant ou por tenant.
  - `dataset_type` (enum: `functional`, `contract`, `performance`, `dr_validation`).
  - `label` (string, <= 128) — nome amigável (`perf-large-2025-01`).
  - `pii_scan_status` (enum: `pending`, `pass`, `fail`).
  - `pii_scan_report_path` (string, opcional) — caminho para artefato de relatório (ex.: `artifacts/pii/seed-run-uuid.json`).
  - `load_test_report_path` (string, opcional) — caminho para relatório k6/Gatling.
  - `created_at` (timestamp with time zone).
- **Relações**:
  - N:1 com `SeedRun`.
  - N:1 com `Tenant` (quando aplicável).
- **Validações**:
  - `dataset_type=performance` exige `load_test_report_path` preenchido após execução de testes de carga.
  - `pii_scan_status=pass` exige `pii_scan_report_path` não vazio.
- **Regras**:
  - Usado para rastrear quais datasets basearam quais execuções de testes de carga/contrato e para auditoria de LGPD.  
  - Permite reuso de datasets entre execuções de testes, desde que os contratos/SLOs continuem válidos.
- **Implementação**:
  - Novo modelo em `backend/apps/foundation/models/seed_dataset_snapshot.py`.

---

### PiiFieldMapping (config declarativa)
- **Descrição**: Mapeamento centralizado de campos PII/PD nos modelos de domínio, com a respectiva regra de anonimização/máscara, usado tanto por seeds quanto pelos scanners de PII.
- **Tipo**: Configuração declarativa (YAML ou estrutura Python) carregada por `backend/apps/foundation/services/seeds.py`.
- **Campos (conceituais)**:
  - `model` (string) — caminho do modelo Django (`app_label.ModelName`, ex.: `customers.Customer`).
  - `field_name` (string).
  - `classification` (enum: `PII_STRICT`, `PII_SENSITIVE`, `PD`, `NON_PII`).
  - `anonymization_rule_id` (string, FK lógica → `AnonymizationRule.id`).
  - `is_business_key` (boolean) — indica chaves de negócio que exigem tratamento especial.
- **Relações**:
  - N:1 com `AnonymizationRule` (via `anonymization_rule_id`).
- **Validações**:
  - Todo campo classificado como `PII_STRICT` ou `PII_SENSITIVE` deve ter uma `anonymization_rule_id` válida.  
  - Campos marcados como `business_key` não podem ser apenas mascarados superficialmente; devem seguir regra forte (hash/tokenização).
- **Regras**:
  - Seeds/anonymização devem sempre consultar esse mapa antes de gerar dados derivados de snapshots de produção.  
  - Scanners de PII devem validar que campos classificados como PII nunca aparecem em logs/test datasets em texto claro.

---

### AnonymizationRule
- **Descrição**: Define como campos PII/PD são transformados em dados sintéticos ou anonimizados de forma irreversível.
- **Campos**:
  - `id` (string, PK lógica; ex.: `hash_sha256`, `tokenize_uuid`, `mask_email`, `fake_brazilian_name`).
  - `strategy` (enum: `hash`, `tokenize`, `mask`, `faker`, `drop`) — como o valor é gerado.
  - `strength` (enum: `strong_irreversible`, `pseudonymization`, `masking_only`) — nível de proteção.
  - `parameters` (JSONB) — parâmetros específicos (salts, formatos, prefixos, etc.).
  - `uses_pgcrypto` (boolean) — indica se a regra utiliza funções `pgcrypto` diretamente.
  - `created_at` / `updated_at` (timestamp with time zone).
- **Relações**:
  - 1:N com `PiiFieldMapping` (campos que utilizam a regra).
- **Validações**:
  - Regras usadas para PII em ambientes não produtivos devem ter `strength=strong_irreversible`.  
  - Quando `uses_pgcrypto=true`, a estratégia deve mapear diretamente para funções disponíveis (`pgp_sym_encrypt`, etc.).
- **Regras**:
  - Implementadas como funções reutilizáveis em `backend/apps/foundation/services/seeds.py` ou módulo dedicado de anonimização; chamadas tanto por seeds quanto por testes utilitários.
- **Implementação**:
  - Pode ser representada via modelos Django ou configuração estática; a decisão pode ser registrada em ADR específico se evoluir.

---

### Tenant (referência)
- **Descrição**: Entidade já existente que representa um espaço lógico isolado (cliente/linha de negócio) e base para RLS multi-tenant.  
  Seeds e datasets sempre operam sob o escopo de um ou mais tenants.
- **Campos relevantes (referência)**:
  - `id` (UUID, PK).
  - `slug` (string).
  - `status` (enum: `pilot`, `production`, `decommissioned`).
- **Regras relevantes**:
  - RLS garante que leituras/escritas respeitem o `tenant_id` corrente (`current_setting('app.tenant_id')`).  
  - Seeds não devem criar dados de teste em tenants marcados como `decommissioned` ou fora do escopo da execução.
- **Implementação**:
  - Modelo existente em `backend/apps/tenancy/models/tenant.py`.

---

## Relationships Diagram (textual)

- `SeedRun` 1 — N `SeedRunEntityMetric`  
- `SeedRun` 1 — N `SeedDatasetSnapshot`  
- `SeedRunEntityMetric` N — 1 `Tenant`  
- `SeedDatasetSnapshot` N — 1 `Tenant` (quando associado a um tenant específico)  
- `AnonymizationRule` 1 — N `PiiFieldMapping`  
- `SeedRun.profile_id` → `SeedProfile.id` (configuracional)  
- `PiiFieldMapping` referencia modelos de domínio existentes (`Tenant`, `Customer`, `Loan`, `Transaction`, `User`, etc.)

---

## State Transitions

### SeedRun.status
- `pending` → `running` → `success`  
- `pending` → `running` → `failed` → (opcional) `rolled_back`  
- `pending` → `skipped` (por exemplo, quando não há tenants ou entidades habilitadas para o perfil)

Regras:
- Transição para `success` exige que todas as `SeedRunEntityMetric` tenham `error_count=0`.  
- Quando uma falha crítica ocorre e um rollback é aplicado, `SeedRun.status` deve ser `rolled_back` e a pipeline deve falhar.  
- Reexecuções idempotentes registram novos `SeedRun` com referência ao mesmo `profile_id`, mas sem duplicar registros de negócio.

### SeedDatasetSnapshot.pii_scan_status
- `pending` → `pass` – quando o scanner de PII não encontra dados pessoais reais.  
- `pending` → `fail` – quando há evidências de PII real ou falha de anonimização.

Regras:
- Datasets com `pii_scan_status != pass` não devem ser usados em testes de carga intensivos ou ambientes compartilhados.  
- Pipelines de CI/CD para ambientes não produtivos falham se qualquer `SeedDatasetSnapshot` relevante ficar em `fail`.

---

## Validation Rules Summary

- Toda métrica ou dataset com `tenant_id` respeita RLS e managers multi-tenant; operações de leitura/escrita são feitas sob o tenant corrente.  
- Perfis de seeds (`SeedProfile`) devem obedecer às volumetrias definidas por Q11 e aos budgets de FinOps (≈10% de custo incremental por ambiente/tenant).  
- Campos classificados como PII/PD em `PiiFieldMapping` devem sempre passar por uma `AnonymizationRule` com `strength=strong_irreversible` em ambientes não produtivos.  
- Logs estruturados relacionados a `SeedRun`/`SeedDatasetSnapshot` não podem incluir valores de PII em texto claro; apenas IDs, hashes, contagens e status.  
- Testes de integração e de carga devem garantir que o uso dos datasets não viola RateLimit/API (`429`, `Retry-After`, cabeçalhos `RateLimit-*`) e mantém SLOs de latência/erro definidos.

---

## Notes

- As entidades de seeds/anonymização são projetadas para serem independentes de domínios específicos, mas referenciam modelos de negócio existentes, garantindo alinhamento com o modelo de domínio único descrito no blueprint (§3.1).  
- Qualquer evolução futura que torne `AnonymizationRule` ou `PiiFieldMapping` persistidos em tabelas próprias deve respeitar migrações zero-downtime (Art. X) e ser acompanhada de ADR.  
- Métricas derivadas de `SeedRunEntityMetric` e `SeedDatasetSnapshot` alimentam dashboards de observabilidade e FinOps (tempo de preparação de ambientes, volumetria por tenant, custo de seeds/testes de carga) e são fundamentais para avaliar se os SLOs e budgets estão sendo cumpridos.  
