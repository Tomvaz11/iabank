# Checklist — API (F‑10 Fundação)

Referências base:
- Workflow: `.github/workflows/frontend-foundation.yml`
- Runbook: `docs/runbooks/frontend-foundation.md`
- Dashboard: `observabilidade/dashboards/frontend-foundation.json`
- Threat model: `docs/security/threat-models/frontend-foundation/v1.0.md`
- Contratos: `contracts/api.yaml`, `contracts/api.previous.yaml`, regras: `contracts/.spectral.yaml`
- CI (últimos runs):
  - push: `push_run.log` (logs locais)
  - PR: (fornecer link do Actions ao último run verde do workflow)
  - manual (sanidade, master): Run ID `19048561651` — logs: `run.log`
- PRs relevantes: #10 (Merge validation v2 final), #11 (Cleanup pós-merge F‑10 CI)

Especificidades obrigatórias deste tema: Spectral, OpenAPI-diff e Pact.

Itens objetivos:
- [x] Spectral (lint) sem erros bloqueantes
  - Evidências: `push_run.log` (Contracts → "Spectral lint"): "No results with a severity of 'error' found!"; regras em `contracts/.spectral.yaml`.
- [x] OpenAPI-diff sem breaking changes (comparação previous → current)
  - Evidências: `push_run.log` (Contracts → "OpenAPI diff"): `"breakingDifferencesFound": false` comparando `contracts/api.previous.yaml` → `contracts/api.yaml`.
- [x] Pact (consumer verification) executado sem falhas
  - Evidências: `push_run.log`/`run.log` (Contracts/Vitest) com interações Pact e testes passando (ex.: `tests/design-system/list-stories.pact.ts`).
- [x] Último run VERDE de PR para o job "Contracts (Spectral, OpenAPI Diff, Pact)"
  - Evidências (PR #12): job verde — https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54406986661
- [x] Runbook atualizado com resultados de contratos
  - Evidências: seção de evidências da F‑10 em `docs/runbooks/frontend-foundation.md` com links dos jobs do PR #12.

Atualizações recentes:
- PR #12 (evidências) mergeado; job de contratos verde — https://github.com/Tomvaz11/iabank/actions/runs/19050934281

Observações:
- Workflow de referência: `.github/workflows/frontend-foundation.yml` (job `contracts`).
- Run manual (sanidade) não executa budgets/visual, mas os contratos rodam; referenciar Run ID `19048561651` quando aplicável.
