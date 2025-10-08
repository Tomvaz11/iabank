---
description: "Template de lista de tarefas para implementacao de feature"
---

# Tasks: [FEATURE NAME]

**Input**: Artefatos em `/specs/[###-feature-name]/` (spec.md, plan.md, research.md, data-model.md, contracts/, tasks.md)  
**Pre-requisitos**: `plan.md` aprovado, pendencias do `/clarify` resolvidas ou registradas

**Testes (Art. III)**: Testes DEVEM ser escritos primeiro e falhar antes da implementacao. Registre o commit/execucao que comprova o estagio vermelho.

**Organizacao**: Tarefas agrupadas por user story (US1, US2, ...) para manter fatias verticais independentes.

## Formato da linha

`[ID] [P?] [USx] Descricao (arquivo-alvo)`  
- **[P]**: Tarefas paralelizaveis (dominios distintos, sem dependencias).  
- **[USx]**: Identificador da user story. Use `FOUND` para fundacoes compartilhadas.  
- Cite caminhos completos (`backend/apps/...`, `frontend/src/...`, `ops/terraform/...`).

## Fase 0: TDD & Contratos Obrigatorios (Art. III, Art. XI)

- [ ] T000 [FOUND] Gerar diffs OpenAPI (`contracts/openapi.yaml`) e Pact, garantir falha antes de implementacao.
- [ ] T001 [FOUND] Escrever testes de integracao (`backend/tests/integration/test_[fluxo].py`) cobrindo cenarios principais e negativos.
- [ ] T002 [FOUND] Adicionar testes de frontend (`frontend/src/.../__tests__/`) quando UI estiver envolvida.
- [ ] T003 [FOUND] Configurar cenarios de k6 (`contracts/perf/[fluxo].js`) com thresholds baseados no SLO.

## Fase 1: Fundamentos Compartilhados (Art. I, II, X, XIII)

- [ ] T010 [FOUND] Atualizar modelos/migrations multi-tenant (`backend/apps/<dominio>/models.py`, `migrations/`) seguindo expand/contract.
- [ ] T011 [FOUND] Ajustar managers/repositorios para aplicar `tenant_id` por padrao.
- [ ] T012 [FOUND] Configurar servicos Celery/Redis ou integracoes compartilhadas.
- [ ] T013 [FOUND] Atualizar documentacao tecnica (`docs/adr/`, `docs/runbooks/`) se necessario.

**Checkpoint**: Fundamentos prontos. User stories podem seguir em paralelo apos validacao.

## Fase 2: User Story 1 - [Titulo] (Prioridade P1)

### Testes (executar antes da implementacao)
- [ ] T100 [P] [US1] Teste de contrato/API (`backend/tests/contract/test_[us1].py`)
- [ ] T101 [P] [US1] Teste de integracao (`backend/tests/integration/test_[us1].py`)
- [ ] T102 [P] [US1] Teste de frontend (`frontend/src/.../__tests__/test_[us1].tsx`) *(se aplicavel)*

### Implementacao
- [ ] T103 [US1] Implementar caso de uso (`backend/apps/<dominio>/application/[use_case].py`)
- [ ] T104 [US1] Ajustar endpoints/views (`backend/apps/<dominio>/api/views.py`, serializers)
- [ ] T105 [US1] Atualizar componentes frontend (`frontend/src/pages/[flow]/`)
- [ ] T106 [US1] Instrumentar logs/traces/metricas conforme Art. VII (`backend/apps/<dominio>/instrumentation.py`)
- [ ] T107 [US1] Atualizar docs/md (`specs/[###-feature-name]/quickstart.md`) com fluxo final

**Checkpoint**: US1 completa, validada via testes escritos na Fase 0.

## Fase 3: User Story 2 - [Titulo] (Prioridade P2)

- [ ] T200 [P] [US2] Teste contrato/integration conforme plano.
- [ ] T201 [US2] Implementacao backend (`backend/apps/<dominio>/...`)
- [ ] T202 [US2] Implementacao frontend (`frontend/src/...`)
- [ ] T203 [US2] Ajustes em pipelines/ci se feature impactar gates.

## Fase 4: User Story 3 - [Titulo] (Prioridade P3)

- [ ] T300 [P] [US3] Testes necessarios (contrato, integracao, e2e).
- [ ] T301 [US3] Implementacoes backend/frontend correspondentes.

## Fase N: Observabilidade, Seguranca e FinOps (Art. VII, XII, XVI)

- [ ] T400 [FOUND] Configurar spans, metricas e dashboards (OpenTelemetry, Prometheus, Sentry).
- [ ] T401 [FOUND] Atualizar politicas RLS (`ops/terraform/modules/postgres/rls_policies.sql`) e testes automaticos.
- [ ] T402 [FOUND] Revisar confidencialidade (mascaramento de PII, criptografia de campo).
- [ ] T403 [FOUND] Ajustar tagging/budgets FinOps (`ops/pipelines/`, `docs/runbooks/finops.md`).

## Fase Final: Handshake Spec-Driven & Revisoes

- [ ] T900 [FOUND] Garantir que `tasks.md` reflita execucao real (Art. XVIII).
- [ ] T901 [FOUND] Atualizar `spec.md`, `plan.md`, ADRs e runbooks com links cruzados.
- [ ] T902 [FOUND] Evidenciar auditoria (checklists, relatorios de conformidade) e anexar nos artefatos.

> Remova fases nao utilizadas e detalhe novas fases quando surgirem historias adicionais. Se alguma tarefa violar a constituicao, registre na tabela de Complexidade do `plan.md` com justificativa e plano de mitigacao.
