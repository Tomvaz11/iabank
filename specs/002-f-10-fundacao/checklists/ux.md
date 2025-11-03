# Checklist — UX (F‑10 Fundação)

Referências base:
- Workflow: `.github/workflows/frontend-foundation.yml`
- Runbook: `docs/runbooks/frontend-foundation.md`
- Dashboard: `observabilidade/dashboards/frontend-foundation.json`
- Threat model: `docs/security/threat-models/frontend-foundation/v1.0.md`
- CI (últimos runs):
  - push: `push_run.log`
  - PR: (fornecer link do Actions ao último run verde do workflow)
  - manual (sanidade, master): Run ID `19048561651` — `run.log`
- PRs relevantes: #10, #11

Especificidades obrigatórias: Storybook + test-runner (axe/WCAG) e Chromatic (condicional em PR).

Itens objetivos:
- [x] Storybook build gerado (estático)
  - Evidências: `push_run.log` (job "Visual & Accessibility Gates" → "Build Storybook estático"), artefatos em `frontend/storybook-static`.
- [ ] Test‑runner do Storybook (axe/WCAG) sem violações (PR)
  - Evidências parciais: em push, `push_run.log` mostra "No accessibility violations detected!" e "Test Suites: 4 passed".
  - O que falta: no PR #12, o job falhou antes (Chromatic), impedindo o test‑runner; necessário um run de PR com o job verde.
- [ ] Chromatic executado em PR com cobertura ≥ 95% por tenant
  - Evidências (PR #12): step "Executar Chromatic" falhou devido a histórico git raso (mensagem "Found only one commit"; `actions/checkout` com `fetch-depth: 1`). Link do job: https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54407027880
  - O que falta: ajuste do fetch-depth (`0`) ou mais commits na branch para Chromatic calcular baseline; então validar cobertura ≥ 95% e anexar o `chromatic-coverage.json` do artefato.
- [ ] Último run VERDE de PR para o job "Visual & Accessibility Gates"
  - O que falta: link do Actions do run de PR com os steps acima concluídos (Chromatic + test‑runner).
- [ ] Runbook atualizado com resultados visuais/A11y
  - O que falta: atualização de `docs/runbooks/frontend-foundation.md` com links para Chromatic/artefatos e resumo das violações axe (idealmente 0) e cobertura.

Notas:
- Em `workflow_dispatch` (sanidade) os steps de Chromatic podem ser pulados — condicional de PR.
