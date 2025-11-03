# Checklist — Geral (F‑10 Fundação)

Referências base:
- Workflow: `.github/workflows/frontend-foundation.yml`
- Runbook: `docs/runbooks/frontend-foundation.md`
- Dashboard: `observabilidade/dashboards/frontend-foundation.json`
- Threat model: `docs/security/threat-models/frontend-foundation/v1.0.md`
- CI (últimos runs):
  - push: `push_run.log` (logs locais)
  - PR: (fornecer link do Actions ao último run verde do workflow)
  - manual (sanidade, master): Run ID `19048561651` (evento `workflow_dispatch`) — logs: `run.log`
- PRs relevantes: #10 (Merge validation v2 final), #11 (Cleanup pós-merge F‑10 CI)

Itens objetivos (marcados apenas com evidências claras):
- [x] Workflow de CI versionado e com jobs esperados (lint/test/contracts/visual/performance/security/threat-model-lint/ci-outage-guard)
  - Evidências: `.github/workflows/frontend-foundation.yml`
- [x] Threat Model Lint OK para `v1.0`
  - Evidências: `push_run.log` (Threat Model Lint) confirma: "[threat-model-lint] Artefato verificado com sucesso" em `docs/security/threat-models/frontend-foundation/v1.0.md`
- [x] Complexidade ciclomática (Radon) dentro do limite (<=10)
  - Evidências: `push_run.log` (Vitest job → "Radon complexity gate"): "Complexidade ciclomática dentro do limite (<=10)."
- [x] Lint (ESLint + FSD boundaries + guard de Zustand) aprovado
  - Evidências (PR #12): job Lint verde — https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54406825581
- [x] Cobertura (Vitest) ≥ 85% (statements/lines/functions)
  - Evidências (PR #12): job Vitest — https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54406870319
  - Resumo do step: "Coverage report from v8" — All files: Statements 95.17%, Lines 95.17%, Functions 88.88%, Branches 84.75 (gate de branches em 84.7 via env).
- [x] Cobertura (Pytest) ≥ 85%
  - Evidências (PR #12): job Vitest → step Pytest — https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54406870319
  - Resumo: linha TOTAL 87% no relatório de cobertura.
- [ ] Verificação de tags `@SC-00x` em PR aprovada
  - Evidências parciais: step "Validar tags @SC-00x no PR" definido no workflow.
  - O que falta: em PR não-chore (o step é pulado para branches que iniciam com `chore/`), link de um PR com o step em "success" (título/corpo contendo @SC-00x).
- [ ] Runbook atualizado com evidências finais da F‑10
  - O que falta: diff/commit ou PR apontando atualização de `docs/runbooks/frontend-foundation.md` com resultados (runs, métricas, gates) e referências aos artefatos.
- [ ] Dashboard atualizado com métricas SC‑001..SC‑005
  - O que falta: diff/commit ou PR atualizando `observabilidade/dashboards/frontend-foundation.json` e inclusão de fontes (ex.: `observabilidade/data/lighthouse-latest.json`).
- [ ] Threat model atualizado (versão vigente) com pontos de CSP/Trusted Types/PII
  - Evidências parciais: arquivo existente `docs/security/threat-models/frontend-foundation/v1.0.md` e lint OK.
  - O que falta: confirmação de atualização pós‑validação (diff/PR) e link do job "Threat Model Lint" no último run verde.

Observações finais:
- Último run manual (sanidade) em master: Run ID `19048561651` (referência: `run.log`).
- Incluir também os PRs #10 e #11 como evidências no runbook/PR final.
 - PR de evidências para CI: #12 — https://github.com/Tomvaz11/iabank/pull/12 (verde: https://github.com/Tomvaz11/iabank/actions/runs/19050934281)
