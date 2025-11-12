# Evidências — F‑10 Fundação Frontend (v1.0)

Data: 2025-11-03
Responsáveis: Frontend Foundation Guild / Platform

## PRs e Runs

- PR #10 — Merge validation v2 final (F‑10) — merged
- PR #11 — Cleanup pós‑merge F‑10 (CI) — merged
- PR #12 — Evidências F‑10 (PR run) — merged
  - Run verde (pull_request): https://github.com/Tomvaz11/iabank/actions/runs/19050934281
  - Jobs (principais):
    - Lint: success
    - Vitest + Pytest: success (All files 95.17/95.17/88.88/84.75; Pytest TOTAL 87%)
    - Contracts (Spectral/OpenAPI/Pact): success
    - Visual & A11y: success (Chromatic executado em PR; test‑runner axe/WCAG sem violações)
    - Performance: success (histórico). ATUALIZAÇÃO 2025-11-08: gates agora são estritos também em PR; continuam publicando artefatos.
    - Security Checks: success (histórico). ATUALIZAÇÃO 2025-11-08: em PR passou a ser fail‑closed (sem fail‑open).
    - Threat Model Lint: success
- Run manual (sanidade em main): ID 19048561651 (workflow_dispatch) — logs locais em `artifacts/local/run.log`.

## Artefatos

- Storybook estático: `frontend/storybook-static/`
- Chromatic coverage: `frontend/chromatic-coverage.json` (em PR; cobertura por tenant tolerante)
- Lighthouse (último): `observabilidade/data/lighthouse-latest.json`
- Lighthouse (resumo usado pelo CI): `artifacts/lighthouse/home.summary.json`
- k6 smoke (PR): artifact `performance-k6-smoke` (upload-artifact)
- SBOM (PR): `sbom/frontend-foundation.json` (após geração/validação)

## Referências

- Workflow: `.github/workflows/frontend-foundation.yml`
- Runbook: `docs/runbooks/frontend-foundation.md`
- Resumo consolidado: `RESUMO_F10_VALIDACAO_E_CI.md`
- Dashboard: `observabilidade/dashboards/frontend-foundation.json`
- Threat model: `docs/security/threat-models/frontend-foundation/v1.0.md`

## Notas de política

- Visual & Performance:
  - Chromatic roda apenas em PR; cobertura por tenant ≥ 95% será endurecida após a issue #13.
  - Budgets Lighthouse/k6 tolerantes em PR; endurecer após a issue #14.
- Segurança:
- fail‑closed em `main/releases/tags`; PR/dispatch com fail‑open e sumário consolidado.

## Follow‑ups (hardening)

- #13 — Elevar cobertura Chromatic ≥ 95% por tenant e remover tolerância no PR.
- #14 — Estabilizar budgets Lighthouse/k6 e tornar os gates de performance rígidos no PR.
