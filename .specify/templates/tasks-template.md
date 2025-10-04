# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category, following the phases defined in this template.
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness against the plan and constitution.
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/src/`
- Paths shown below are examples. The `/tasks` command will use the structure from `plan.md`.

---
## Phase 3.1: Setup & Governance
<!-- Tasks related to project setup, dependency management, and governance principles like SRE and FinOps -->
<!-- Example: [ ] T001 [P] Definir SLIs e SLOs para latência e disponibilidade do serviço X em `docs/sre/x.md` -->
<!-- Example: [ ] T002 [P] Adicionar tags de FinOps 'cost-center=Y' aos novos recursos Terraform do serviço X -->
<!-- Example: [ ] T003 Atualizar o documento RIPD/ROPA em `docs/lgpd/servico-x.md` com o novo fluxo de dados -->

## Phase 3.2: Design & Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
<!-- Tasks related to creating and validating contracts, and writing failing integration/security tests -->
<!-- Example: [ ] T006 [P] Criar/atualizar contrato OpenAPI em `contracts/` e validar com linter -->
<!-- Example: [ ] T007 [P] Escrever teste de autorização para garantir que o perfil Z não acesse o recurso X, conforme matriz RBAC -->
<!-- Example: [ ] T008 Conduzir threat modeling (STRIDE) para o fluxo de checkout e registrar em `docs/security/threat-model-checkout.md` -->
<!-- Example: [ ] T009 Escrever teste de RLS para garantir que `tenant_id` restrinja consultas em `backend/src/loans/tests/test_rls.py` -->

## Phase 3.3: Core Implementation (ONLY after tests are failing)
<!-- Tasks for creating models, services, and endpoints to make the tests pass -->
<!-- Example: [ ] T011 [P] Implementar `user` model em `backend/src/models/user.py` com criptografia para campos PII -->
<!-- Example: [ ] T012 [P] Implementar query manager multi-tenant aplicando `tenant_id` por padrão em `backend/src/users/query_manager.py` -->

## Phase 3.4: Integration & Security Hardening
<!-- Tasks for connecting components, implementing security controls, and creating infrastructure alinhados aos ADR-010/011/012 -->
<!-- Example: [ ] T017 Implementar middleware de autenticação que obtenha segredos via Vault/KMS conforme ADR-010 -->
<!-- Example: [ ] T018 [P] Configurar mascaramento de PII em logs/traces seguindo ADR-010 e validar via testes automatizados -->
<!-- Example: [ ] T019 Documentar e aplicar `CREATE POLICY` RLS para `loans` em `backend/src/loans/migrations/00xx_add_rls.py` -->

## Phase 3.5: Polish & Validation
<!-- Tasks for final unit tests, performance/security scanning, documentation, and manual validation -->
<!-- Example: [ ] T022 Executar GameDay para simular falha do banco de dados do serviço X e validar o runbook de recuperação -->
<!-- Example: [ ] T023 Validar se logs de auditoria para o serviço X estão sendo enviados para o bucket WORM -->
<!-- Example: [ ] T024 Atualizar runbook de incidente em `docs/runbooks/servico-x.md` com lições aprendidas do GameDay -->
---

## Task Generation Rules
*Applied by the /tasks command during execution*

1.  **From Contracts**: Each endpoint/message → contract test task [P] + implementation task.
2.  **From Data Model**: Each entity → model creation task [P].
3.  **From User Stories**: Each acceptance criteria → integration test [P].
4.  **From Constitution**: Each relevant principle → validation/setup tasks (e.g., SRE, FinOps, Security tasks).

## Validation Checklist
*GATE: Checked by the /tasks command before returning*

- [ ] All contracts have corresponding tests.
- [ ] All entities have model tasks.
- [ ] All tests come before implementation.
- [ ] All constitutional principles are represented by at least one task.
- [ ] Parallel tasks are truly independent.
