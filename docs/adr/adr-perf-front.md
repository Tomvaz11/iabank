# ADR — Performance Frontend (Lighthouse + k6)

Status: Proposto (planejado no /speckit.plan 2025-10-14)

Contexto
- Art. IX (Pipeline CI) exige gates de performance. Em 2025-10-12 a clarificação definiu uso conjunto: k6 (APIs/backend/edge) e Lighthouse/Playwright‑lighthouse (frontend, budgets UX).

Decisão
- Frontend adotará Lighthouse como gate principal de UX: budgets LCP ≤ 2.5s p95, TTI ≤ 3.5s p95, CLS ≤ 0.1.
- k6 permanece para smoke/perf de endpoints críticos expostos ao frontend (com `X-Tenant-Id` e `traceparent`).
- Orquestração no job `performance` do workflow `ci/frontend-foundation.yml`.
- Falhas de budget bloqueiam PRs (fail-closed) em branches de release e `main`; em branches de feature, o gate é fail-open, mas monitora e marca `@SC-001`.

Consequências
- O repositório terá `frontend/lighthouse.config.mjs` com budgets e `tests/performance/frontend-smoke.js` para k6.
- Devemos manter dashboards com distribuição de LCP/TTI/CLS e histórico por tenant (ver observability/dashboards/frontend-foundation.json).
- Mudanças de budgets exigem atualização deste ADR e consenso do Frontend Guild + SRE.

Referências
- Constituição v5.2.0 — Art. IX
- Clarifications 2025-10-12 (Perf-Front)
- BLUEPRINT_ARQUITETURAL.md §4
