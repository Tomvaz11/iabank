# Resumo detalhado — F‑10, Validação e CI

Data: 2025-11-03
Autor: Assistente (Codex CLI)

Este documento consolida o ciclo de encerramento da F‑10: contexto, decisões (PORQUÊ), alterações (O QUÊ), implementação (COMO), estado do CI e próximos passos. Use este arquivo como ponto de partida (peça ao assistente para “ler e seguir este resumo”).

## Contexto

- F‑10 (“Fundação Frontend FSD e UI Compartilhada”) implementada e integrada na branch padrão `main` (migração concluída a partir de `master`).
- Objetivo: estabilizar o CI principal, fechar validação final, preparar o pós‑merge segundo o Spec‑Kit.

## Decisões (PORQUÊ)

1) Padronizar CI na branch base `main` (mantendo compatibilidade com `master` durante a transição).
2) Execuções manuais (`workflow_dispatch`) são para sanidade — sem “falsos vermelhos”.
3) Evitar instabilidades em `push` de branches utilitárias (Chromatic/Lighthouse/DAST apenas onde faz sentido).

## Alterações (O QUÊ) e Implementação (COMO)

1) Workflow principal do CI: `.github/workflows/frontend-foundation.yml`:1
   - Gatilhos: `pull_request` (main/master/develop/feature/**), `push` (main/develop/feature/**/chore/**), `workflow_dispatch`.
   - Diagnóstico: job `CI Diagnostics` imprime contexto e garante logs.
   - Visual & A11y:
     - Chromatic roda apenas em `pull_request` se houver `CHROMATIC_PROJECT_TOKEN` (via `env`, não em `if: secrets.*`).
     - Em `workflow_dispatch`, o job Visual & A11y é pulado (sanidade).
   - Performance Budgets:
     - Executa somente em `pull_request` e em `main` (compatível com `master`); nunca em `workflow_dispatch` (evita falso vermelho no manual).
   - Segurança:
     - `CI_ENFORCE_FULL_SECURITY` ativo em `main/releases/tags` (fail‑closed; compatível com `master`). Em PR/branches/dispatch → fail‑open, com sumário consolidado.
     - DAST (ZAP) executa apenas em PR e `main` (compatível com `master`).
   - Testes:
     - Vitest: statements/lines/functions ≥85%; branches via env `FOUNDATION_COVERAGE_BRANCHES`.
     - Pytest: serviço Postgres 15 + envs `FOUNDATION_DB_*` no step dedicado.
     - Em `workflow_dispatch`, steps de coverage ficam `continue-on-error` (sanidade).
   - Robustez do YAML:
     - Ajustado uso de `secrets.*` em `if:` (agora via `env.*`) para evitar “Invalid workflow file”.
     - `pgcrypto`: executar via `python -m scripts.security.check_pgcrypto` (evita `ModuleNotFoundError`).

2) Testes (backend/frontend)
   - `backend/apps/foundation/tests/test_list_tenant_success_metrics_api.py`:1 — caso de `X‑Tenant‑Id` usa `uuid.uuid4()` para mismatch robusto.
   - `tests/workflows/test_security_job.py`:1 — lê `.github/workflows/frontend-foundation.yml` com fallback para o caminho legado.

3) Limpeza pós‑merge
   - Removido workflow legado duplicado: `.github/workflows/ci/frontend-foundation.yml`.
   - Removido submódulo acidental `codex-action` e adicionado ao `.gitignore`.

## Estado do CI (evidências)

- Push (branch utilitária `chore/ci-nudge`): SUCESSO
  - Lint: PASS; Vitest/Pytest: PASS; Contracts: PASS; Visual & A11y (axe/WCAG): PASS; Segurança: PASS (fail‑open); Performance: pulado.

- Manual (workflow_dispatch em `main`): SUCESSO — Run ID: `19048561651` (histórico originalmente executado em `master` antes da migração)
  - Visual & A11y: pulado integralmente (sanidade)
  - Performance Budgets: pulado integralmente (sanidade)
  - Segurança: fail‑open; DAST não executa (somente PR/protegidas); sumário consolidado OK
  - Demais jobs (Lint, Vitest/Pytest, Contracts, Threat Model Lint, CI Outage Guard): PASS

- PR de evidências (pull_request): SUCESSO — PR #12 (merged)
  - Run verde: https://github.com/Tomvaz11/iabank/actions/runs/19050934281
  - Lint, Vitest/Pytest, Contracts, Visual & A11y, Performance, Security, Threat Model: PASS (Visual/Performance tolerantes no PR)

## Como rodar

1) Manual (sanidade em `main`):
```bash
gh workflow run .github/workflows/frontend-foundation.yml --ref main
gh run list --workflow=".github/workflows/frontend-foundation.yml" --event workflow_dispatch --branch main --limit 3
gh run view <RUN_ID> --log
```

2) PR (gates completos):
```bash
gh pr checks <PR_NUM>
gh run list --workflow=frontend-foundation.yml --event pull_request --limit 3
```

## Pós‑merge (executar conforme PASSO_A_PASSO_POS_F10.md)

- Telemetria/segurança: `pnpm foundation:otel verify --tenant tenant-alfa` (evidências de PII masking e correlação de traces) — anexar ao runbook.
- Performance: `pnpm perf:lighthouse` e `pnpm perf:smoke:ci` (publicar artefatos no dashboard).
- Contratos (opcional local): `pnpm openapi && pnpm pact:verify`.
- FinOps: `pnpm finops:report` (anexar ao dashboard/runbook).
- Documentos: atualizar
  - `docs/runbooks/frontend-foundation.md`:1
  - `observabilidade/dashboards/frontend-foundation.json`:1
  - `docs/security/threat-models/frontend-foundation/<release>.md`:1

## Itens pendentes/ajustes possíveis

- (Estratégia) Migrar default branch para `main` no futuro (gatilhos já compatíveis com ambos).
- (Política) Opcional: endurecer Segurança (fail‑closed) também em PRs cujo base seja `main` (hoje PRs seguem fail‑open; `main/releases/tags` já estão fail‑closed; compatível com `master` durante transição).

## Referências

- Passo a passo: `PASSO_A_PASSO_POS_F10.md`:1
- Workflow de CI (atual): `.github/workflows/frontend-foundation.yml`:1
- Teste de workflow (compat): `tests/workflows/test_security_job.py`:1
- Teste de tenant header (fix): `backend/apps/foundation/tests/test_list_tenant_success_metrics_api.py`:1
