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
- [ ] Job "Performance Budgets" executado e verde (PR ou master/main)
  - Evidências (PR #12): falha ao resolver ação `grafana/setup-k6-action@v0.4.0` — https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54407027840
  - O que falta: link do run (PR/master) com job concluído, incluindo Lighthouse e k6.
- [x] Artefato Lighthouse presente e dentro dos budgets
  - Evidências: `observabilidade/data/lighthouse-latest.json` com `lcp=713ms`, `tti=718ms`, `tbt=0`, `cls=0`, budgets (`lcp<=2500ms`, `tti<=3000ms`, `tbt<=200ms`, `cls<=0.1`).
- [ ] k6 smoke executado e artefato publicado
  - Evidências parciais: script `tests/performance/frontend-smoke.js` e testes Python validam existência.
  - O que falta: link do step "Executar k6 smoke" no Actions com upload do artefato `artifacts/k6-smoke.json`.
- [ ] Dashboard atualizado com métricas de performance
  - O que falta: diff/PR atualizando `observabilidade/dashboards/frontend-foundation.json` incorporando resultados recentes (Lighthouse/k6), além de anexos/artefatos dos runs.

Notas:
- Em `workflow_dispatch` (sanidade) budgets de performance são pulados por design; validar via PR/master.
