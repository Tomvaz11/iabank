# Implementation Plan: F-11 Automacao de Seeds e Dados de Teste

**Branch**: `[003-seed-data-automation]` | **Date**: 2025-11-14 | **Spec**: `specs/003-seed-data-automation/spec.md`
**Input**: Feature specification from `/specs/003-seed-data-automation/spec.md`

**Note**: Este plano segue o fluxo `/speckit.plan` descrito em `.specify/templates/commands/plan.md`, alinhado à Constituição v5.2.0.

## Summary

Esta feature, definida em `specs/003-seed-data-automation/spec.md`, implementa a automação de seeds e dados de teste no monolito modular Django/DRF sobre PostgreSQL, por meio de um comando padronizado `seed_data` idempotente, um catálogo único de factories com `factory-boy` e geração de datasets sintéticos para ambientes não produtivos (dev/hom/performance/DR).  
O plano integra seeds, anonimização forte de PII/PD e datasets de carga aos pipelines de CI/CD e GitOps (Argo CD + Terraform), garantindo aderência à Constituição (Art. I, III, IV, VII, VIII, IX, XI, XIII, XVIII), aos blueprints (`BLUEPRINT_ARQUITETURAL.md`, `adicoes_blueprint.md`) e aos ADRs relevantes (incluindo ADR-010/ADR-012), com suporte explícito a multi-tenant com RLS, estratégia de DR e limites de RateLimit/API `/api/v1`.  
Lacunas adicionais serão rastreadas via `clarify.md` (a ser criado se necessário) e resolvidas nas Fases 0 e 1 deste plano.

## Technical Context

Preenche o plano técnico para a feature F-11, referenciando a Constituição e os blueprints. `[NEEDS CLARIFICATION]` é usado apenas quando a decisão ainda depende de pesquisa adicional.

**Language/Version**: Python 3.11 (backend monolito modular Django/DRF), conforme Art. I da Constituição e instruções do projeto.  
**Primary Dependencies**: Django 4.2 LTS, Django REST Framework 3.15, Celery 5.3 + Redis 7 (para seeds assíncronas e datasets de carga), `factory-boy` como catálogo único de factories, PostgreSQL 15 com `pgcrypto` e RLS multi-tenant, OpenTelemetry SDK + Sentry para observabilidade, ferramentas de carga (k6 ou Gatling equivalente) e Pact/OpenAPI 3.1 para contratos; alinhado a `BLUEPRINT_ARQUITETURAL.md` (§§3.1, 6, 26) e aos ADR-010/ADR-012.  
**Storage**: PostgreSQL 15 multi-tenant com banco compartilhado, RLS por tenant e uso de `pgcrypto` para criptografia de dados sensíveis e suporte a anonimização irreversível; nenhum novo datastore é introduzido para esta feature.  
**Testing**: `pytest` + `pytest-django`, client de teste do DRF para testes de integração-primeiro, factories `factory-boy` reaproveitadas entre testes unitários/integração/contrato/carga, Pact para contratos da API `/api/v1`, testes de carga com k6 (ou Gatling equivalente) e scanners de PII para validar anonimização; obedecendo Art. III (TDD) e Art. IV (integração-primeiro) e Art. IX (gates de qualidade/performance).  
**Target Platform**: Ambientes Linux em Kubernetes (dev, homologação, performance e DR) provisionados por Terraform e sincronizados via Argo CD, com pipelines de CI/CD integrando estágios de seeds, anonimização, verificação de PII e testes de carga.  
**Project Type**: Aplicação web backend em monorepo com monolito modular Django/DRF; o frontend React/TypeScript/Vite em FSD permanece inalterado e apenas consome dados de teste mais consistentes via `/api/v1`.  
**Performance Goals**: Preparar dados de teste (seeds + anonimização + datasets sintéticos) em até ~10 minutos em 95% dos deploys de dev/hom (SLO de preparação de ambiente), respeitando os SLOs de latência/throughput/Saturação da API e de RateLimit definidos em `adicoes_blueprint.md` (itens 1, 3, 8, 11).  
**Constraints**: Execução idempotente e segura do comando `seed_data` (reexecução segura inclusive em cenários de restauração/DR); apenas dados sintéticos ou irreversivelmente anonimizados em ambientes não produtivos; nenhuma seed de dados de negócio (mesmo sintéticos) em produção, apenas seeds técnicas estritamente necessárias; respeito a RateLimit e políticas LGPD (Art. XIII), a migrações zero-downtime (Art. X) e a budgets de FinOps (custo incremental de testes de carga limitado a ~10% do budget de cada ambiente/tenant).  
**Scale/Scope**: Volumetrias parametrizáveis `small`/`medium`/`large` por ambiente/tenant alinhadas às faixas de Q11 (≈50/200/500 registros por entidade/tenant em dev/hom; ≈5.000/20.000/50.000 em performance), cobrindo entidades principais do domínio (clientes, contas/usuários, contratos/emprestimos, parcelas, transações, limites/rate-limiters) e integrando-se a pipelines de CI/CD, DR e datasets de carga.

### Contexto Expandido

**Backend**: Monolito modular Django/DRF existente sob `backend/`, com apps centrais `backend/apps/foundation`, `backend/apps/tenancy` e `backend/apps/contracts`; o comando `seed_data` será implementado como management command Django em `backend/apps/foundation/management/commands/seed_data.py`, orquestrando seeds de todos os apps e reutilizando `backend/apps/tenancy/management/commands/seed_foundation_tenants.py` como sub-etapa/serviço, conforme decidido em `research.md` (§1).  
**Frontend**: Frontend React/TypeScript/Vite em FSD sob `frontend/` permanece estruturalmente inalterado; apenas se beneficia de datasets mais previsíveis/consistentes nas chamadas para `/api/v1`, inclusive para ambientes efêmeros e review apps, conforme Art. I e blueprints de UI.  
**Async/Infra**: Para volumetrias elevadas e geração de datasets de carga, seeds poderão ser executadas de forma assíncrona via Celery/Redis com tarefas idempotentes, backoff exponencial e DLQ conforme §26 e os princípios de idempotência já modelados em `backend/apps/foundation/idempotency.py`; `seed_data` oferecerá modos síncrono e assíncrono, com filas dedicadas para seeds (`seed_data_default`) e para cargas de performance/DR (`seed_data_perf`), com concorrência controlada por settings (por exemplo, `SEED_DATA_MAX_CONCURRENCY`), conforme `research.md` (§2).  
**Persistência/Dados**: PostgreSQL 15 com RLS por tenant, modelos de domínio descritos no `BLUEPRINT_ARQUITETURAL.md` (§3.1) e políticas de migração zero-downtime (Art. X); o catálogo de factories e os seeds declarativos mapearão explicitamente campos PII/PD, regras de mascaramento/anonimização forte (inclusive para chaves de negócio) e uso de `pgcrypto`/RLS para garantir confidencialidade; arquivos declarativos de seeds serão armazenados em YAML sob `backend/apps/foundation/seeds/config/`, organizados por ambiente/perfil de volumetria (por exemplo, `dev/small.yaml`, `perf/large.yaml`), conforme `research.md` (§3).  
**Testing Detalhado**: Testes de integração-primeiro com banco real e cliente DRF para validar seeds, anonimização de PII, comportamento multi-tenant com RLS e respeito a RateLimit/API (`429`, `Retry-After`, cabeçalhos `RateLimit-*`), além de testes unitários dos serviços de seed/anonimização e testes de contrato (Pact/OpenAPI) e de carga (k6/Gatling) usados contra `/api/v1`; scanners de PII baseados em padrões (CPF/CNPJ, e-mail, telefone, CEP etc.) e amostragem automatizada, implementados em `tests/security/test_pii_scanner_seeds.py`, apoiarão a verificação de anonimização, conforme `research.md` (§4).  
**Observabilidade**: Instrumentação de seeds/anonimização/datasets com OpenTelemetry e W3C Trace Context, gerando métricas (tempo/volume por entidade/tenant, taxa de falhas, consumo de recursos), traces e logs estruturados em JSON sem vazamento de PII, integrados a Sentry e aos exporters já definidos em ADR-012; relatórios de execução por entidade/tenant serão correlacionáveis via IDs de trace/spans.  
**Segurança/Compliance**: Conformidade com LGPD e políticas internas (Art. XII, XIII, XVI): apenas dados sintéticos ou irreversivelmente anonimizados em ambientes não produtivos, nenhuma PII real em logs ou datasets de teste, mapeamento explícito de PII/PD por modelo, políticas de mascaramento fortes, uso de `pgcrypto`/Vault Transit quando aplicável, e validação automatizada com scanners de PII e amostragem; produção limitada a seeds técnicas com change management registrado.  
**Performance Targets**: SLO de preparação de ambientes (dados prontos em ≤10 minutos em 95% dos deploys dev/hom), limites de consumo de API por ambiente/tenant respeitando RateLimit e SLOs de latência/throughput, metas de não saturar o banco PostgreSQL durante seeds de volumetria alta (controle de batch/concurrency) e de manter o impacto financeiro dentro dos budgets de FinOps (≈10% de custo incremental máximo por tenant/ambiente).  
**Restrições Operacionais**: TDD estrito (Art. III) e integração-primeiro (Art. IV) para toda lógica de seeds/anonimização; migrações zero-downtime com estratégia expand/contract ao introduzir colunas/flags necessários para seeds (Art. X); enforcement de RLS multi-tenant e managers específicos para evitar cross-tenant; respeito às janelas de manutenção/DR definidas nos blueprints; execução de seeds integrada aos pipelines de CI/CD e GitOps com gates baseados em SLOs, SAST/DAST/SCA, SBOM e métricas DORA.  
**Escopo/Impacto**: Impacta principalmente `backend/apps/foundation`, `backend/apps/tenancy`, `backend/apps/contracts`, `contracts/` (OpenAPI/Pact), `tests/` (unitários/integração/contratos/performance) e pipelines de CI/CD/GitOps; decisões detalhadas sobre o posicionamento do comando `seed_data`, diretório de configs declarativas e catálogo de factories centralizado foram consolidadas em `research.md` (§§1, 3, 5).

## Constitution Check

*GATE: Validar antes da Fase 0 e reconfirmar após o desenho de Fase 1.*

- [x] **Art. III - TDD**: Toda implementação de `seed_data`, catálogo de factories `factory-boy` e serviços de anonimização será guiada por testes de integração falhando primeiro, usando banco real e cliente DRF (arquivos previstos como `backend/apps/foundation/tests/test_seed_data_command_integration.py`, `backend/apps/tenancy/tests/test_seed_data_multi_tenant.py`, `tests/performance/test_seed_data_load_profiles.py`), garantindo TDD estrito antes de qualquer código de implementação.  
- [x] **Art. VIII - Lançamento Seguro**: A execução de seeds/anonimização será gateada por flags/configuração de ambiente, com suporte a modo `dry-run`, transações de banco para evitar estados parcialmente populados e rollback claro em caso de falha; seeds assíncronas via Celery/Redis seguirão estratégia de idempotência, backoff e DLQ descrita no §26, com error budgets e limites de impacto definidos para cada ambiente/tenant.  
- [x] **Art. IX - Pipeline CI**: O pipeline de CI incluirá estágios para rodar o comando `seed_data` em ambiente controlado, executar testes de integração/contrato/carga relevantes, aplicar SAST/DAST/SCA, gerar SBOM e checar gates de performance (via k6/Gatling), garantindo que seeds e datasets não quebrem os requisitos mínimos de cobertura, complexidade e latência.  
- [x] **Art. XI - Governança de API**: Contratos OpenAPI 3.1 e Pact para `/api/v1` serão atualizados/estendidos em `contracts/` para cobrir cenários dependentes de seeds/datasets sintéticos, mantendo versionamento por URL (`/api/v1`) e diffs controlados; erros seguirão RFC 9457 e semântica de RateLimit com `429`, `Retry-After` e cabeçalhos `RateLimit-*`.  
- [x] **Art. XIII - Multi-tenant & LGPD**: Seeds e factories respeitarão o modelo multi-tenant com banco compartilhado e RLS por tenant (managers/queries sempre filtrando por tenant), garantindo isolamento de dados entre tenants e anonimização forte de PII/PD; seeds serão segmentadas por ambiente/tenant, e produção ficará restrita a seeds técnicas, com evidências de conformidade e auditoria.  
- [x] **Art. XVIII - Fluxo Spec-Driven**: O fluxo `/constitution -> /specify -> /clarify -> /plan -> /tasks` será mantido via `specs/003-seed-data-automation/spec.md`, este `plan.md`, `research.md`, futuros `clarify.md`/`tasks.md` e contratos em `contracts/`; qualquer pendência marcada como `[NEEDS CLARIFICATION]` nesta fase será endereçada em `research.md` e rastreada em `/clarify` se permanecer aberta.

## Project Structure

### Documentacao (esta feature)

Árvore planejada para a documentação de F-11 em `/specs/003-seed-data-automation/`, alinhada ao fluxo `/constitution -> /specify -> /clarify -> /plan -> /tasks`:

```
specs/003-seed-data-automation/
|-- spec.md                      # Especificação funcional da feature (já existente)
|-- plan.md                      # Este plano de implementação
|-- research.md                  # Fase 0: decisões de pesquisa, trade-offs e resolução de NEEDS CLARIFICATION
|-- data-model.md                # Fase 1: modelo de dados/entidades para seeds, factories e datasets
|-- quickstart.md                # Fase 1: guia de uso de `seed_data`, factories e perfis de volumetria
|-- contracts/
|   `-- seed-data-openapi.yaml   # Contratos OpenAPI/Pact relacionados a seeds/datasets para `/api/v1`
|-- checklists/
|   `-- requirements.md          # Checklist de requisitos da feature (já existente)
|-- arquivo_morto_historico/     # Arquivos de histórico/arquivo morto (já existentes)
|   `-- ...
`-- tasks.md                     # Backlog de tarefas gerado via `/tasks`, mantendo rastreio Art. XVIII (a criar)
```

### Codigo-Fonte (repositorio)

Diretórios reais do repositório que devem ser afetados pela implementação desta feature, mantendo a arquitetura em camadas e modularidade (Art. I e II):

```
backend/
|-- apps/
|   |-- foundation/
|   |   |-- management/commands/seed_data.py       # Novo management command central de seeds (planejado)
|   |   |-- factories/                             # Novo catálogo único de factories `factory-boy` (planejado)
|   |   |-- services/seeds.py                      # Serviços de orquestração de seeds/anonimização (planejado)
|   |   `-- tests/                                 # Testes unitários/integração para seeds/factories
|   |
|   |-- tenancy/
|   |   |-- management/commands/seed_foundation_tenants.py  # Comando existente, reutilizado/orquestrado por `seed_data`
|   |   `-- tests/                                 # Testes multi-tenant/RLS para seeds
|   |
|   `-- contracts/
|       `-- tests/                                 # Testes de contrato para `/api/v1` com datasets sintéticos
|
|-- config/                                        # Configurações de ambiente/feature flags e perfis de volumetria
contracts/                                         # OpenAPI 3.1, Pact e artefatos de contrato atualizados
tests/
|-- backend/                                       # Testes auxiliares de serviços/configurações
|-- contracts/                                     # Testes de contrato API (Pact/OpenAPI)
|-- performance/                                   # Testes de carga (k6/Gatling) focados em seeds/datasets
`-- security/                                      # Testes de segurança/PII scanners relacionados a datasets de teste
```

**Structure Decision**: A estrutura proposta mantém a lógica de seeds e o catálogo de factories dentro de apps existentes do monolito (`foundation`, `tenancy`, `contracts`), evitando criação de um novo app dedicado apenas a seeds e preservando a modularidade em torno dos domínios de negócio (Art. I/II). O comando `seed_data` vive ao lado de outros management commands, enquanto os serviços de seeds/anonimização residem na camada de serviços da aplicação, reutilizando utilitários de idempotência e métricas já presentes em `foundation`. O catálogo único de factories sob `foundation/factories/` permite uso consistente de dados sintéticos/anonimizados em testes unitários, de integração, contrato e carga, bem como no próprio comando de seeds, reduzindo duplicação e garantindo alinhamento com o modelo de domínio descrito no blueprint.

## Complexity Tracking

*Preencha somente quando algum item da Constitution Check estiver marcado como N/A/violado. Cada linha deve citar explicitamente o artigo impactado e o ADR/clarify que respalda a exceção.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
|           |            |                                     |
