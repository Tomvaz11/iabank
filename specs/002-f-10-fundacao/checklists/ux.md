# Checklist — UX (F‑10 Fundação)

Referências base:
- Workflow: `.github/workflows/frontend-foundation.yml`
- Runbook: `docs/runbooks/frontend-foundation.md`
- Dashboard: `observabilidade/dashboards/frontend-foundation.json`
- Threat model: `docs/security/threat-models/frontend-foundation/v1.0.md`
- CI (últimos runs):
  - push: `artifacts/local/push_run.log`
  - PR: (fornecer link do Actions ao último run verde do workflow)
  - manual (sanidade, main): Run ID `19048561651` — `artifacts/local/run.log`.
- PRs relevantes: #10, #11

Especificidades obrigatórias: Storybook + test-runner (axe/WCAG) e Chromatic (condicional em PR).

Itens objetivos:
- [x] Storybook build gerado (estático)
  - Evidências: `artifacts/local/push_run.log` (job "Visual & Accessibility Gates" → "Build Storybook estático"), artefatos em `frontend/storybook-static`.
- [x] Test‑runner do Storybook (axe/WCAG) sem violações (PR)
  - Evidências (PR #12): job Visual verde (test‑runner executado sem violações) — https://github.com/Tomvaz11/iabank/actions/runs/19050934281
- [x] Chromatic executado em PR (condicional)
  - Evidências: PR #12 — build publicado e cobertura validada (job Visual verde após ajustes). Run: https://github.com/Tomvaz11/iabank/actions/runs/19050934281
  - Observação: cobertura por tenant (≥95%) agora é gate rígido em PR — resolvido no PR #16 (follow‑up #13 concluído).
- [x] Último run VERDE de PR para o job "Visual & Accessibility Gates"
  - Evidências: PR #12 — job verde — https://github.com/Tomvaz11/iabank/actions/runs/19050934281
- [x] Runbook atualizado com resultados visuais/A11y
  - Evidências: seção "Evidências F‑10"/"Evidências PR #12 — run verde" em `docs/runbooks/frontend-foundation.md`.

Atualizações recentes:
- PR #12 mergeado; run verde do job Visual: https://github.com/Tomvaz11/iabank/actions/runs/19050934281
- Cobertura por tenant ≥ 95% ficará para o follow‑up (issue #13); no PR atual, o step de cobertura está tolerante e publica artefatos.

Notas:
- Em `workflow_dispatch` (sanidade) os steps de Chromatic podem ser pulados — condicional de PR.
