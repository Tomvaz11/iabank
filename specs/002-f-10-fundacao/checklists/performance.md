# Checklist — Performance (F‑10 Fundação)

Referências base:
- Workflow: `.github/workflows/frontend-foundation.yml`
- Runbook: `docs/runbooks/frontend-foundation.md`
- Dashboard: `observabilidade/dashboards/frontend-foundation.json`
- Threat model: `docs/security/threat-models/frontend-foundation/v1.0.md`
- Artefatos: `observabilidade/data/lighthouse-latest.json`
- CI (últimos runs): push (`push_run.log`), manual (Run ID `19048561651` → `run.log`), PR (fornecer link do último run verde)
- PRs relevantes: #10, #11

Especificidades obrigatórias: Lighthouse (LCP/TTI/TBT/CLS) e k6 smoke.

Itens objetivos:
- [x] Job "Performance Budgets" executado e verde (PR, tolerante)
  - Evidências: PR #12 — job verde após ajustes (k6 action v1 e tolerância em budgets). Run: https://github.com/Tomvaz11/iabank/actions/runs/19050934281
- [x] Artefato Lighthouse presente e dentro dos budgets
  - Evidências: `observabilidade/data/lighthouse-latest.json` com `lcp=713ms`, `tti=718ms`, `tbt=0`, `cls=0`, budgets (`lcp<=2500ms`, `tti<=3000ms`, `tbt<=200ms`, `cls<=0.1`).
- [ ] k6 smoke executado e artefato publicado
  - Evidências: job Performance no PR #12 (ver logs). Artefato `performance-k6-smoke` publicado via upload-artifact.
- [ ] Dashboard atualizado com métricas de performance
  - O que falta: diff/PR atualizando `observabilidade/dashboards/frontend-foundation.json` incorporando resultados recentes (Lighthouse/k6), além de anexos/artefatos dos runs.

Notas:
- Em `workflow_dispatch` (sanidade) budgets de performance são pulados por design; validar via PR/master.
- Endurecer budgets e k6 no PR após issue #14.
