# Release Notes — F‑10 Fundação Frontend (v1.0)

Data: 2025-11-03

## Resumo

O quê
- Fundação Frontend FSD e UI Compartilhada (F‑10): base de arquitetura feature‑sliced, Storybook/Chromatic, integrações com TanStack Query/Zustand, propagação OTEL no cliente, pactos FE/BE e critérios de acessibilidade.

Por quê
- Estabelecer baseline consistente para desenvolvimento frontend multi‑tenant, com governança de UI, cobertura de testes ≥ 85%, contratos estáveis e políticas de segurança/observabilidade padronizadas.

Decisões principais de CI
- Branch base `main` (compatível com `master` durante transição).
- Gatilhos: `pull_request`, `push` (main/develop/feature/**/chore/**) e `workflow_dispatch` (sanidade).
- Visual & A11y: Chromatic executa em PR; pulado em `workflow_dispatch` (evita falso vermelho manual).
- Performance Budgets: executa em PR e `main` (compatível com `master`); pulado em `workflow_dispatch`.
- Segurança: `fail‑closed` em `main/releases/tags`; PR/dispatch em `fail‑open` com sumário consolidado. DAST (ZAP baseline) em PR e `main`.
- Testes: Vitest/Pytest com cobertura alvo ≥ 85%. Postgres 15 provisionado no CI para backend.
- Robustez do YAML: uso de `env.*` nas condições; `pgcrypto` validado via script dedicado.

Artefatos e links
- Resumo executivo: `RESUMO_F10_VALIDACAO_E_CI.md`
- Runbook: `docs/runbooks/frontend-foundation.md`
- Evidências: `docs/runbooks/evidences/frontend-foundation/v1.0/README.md`
- Dashboard: `observabilidade/dashboards/frontend-foundation.json`
- Lighthouse (mais recente): `observabilidade/data/lighthouse-latest.json`
- k6 smoke (PR #12): artefato `performance-k6-smoke` (run de PR abaixo)

## Runs
- workflow_dispatch (main): https://github.com/Tomvaz11/iabank/actions/runs/19048561651 (SUCESSO; Visual/Performance pulados por política; histórico pré-migração em `master`).
- PR #12 (run verde): https://github.com/Tomvaz11/iabank/actions/runs/19050934281 (Lint, Vitest/Pytest, Contracts, Visual & A11y, Performance, Security, Threat Model)

## PRs correlatos
- #10 — Merge validation v2 final (F‑10)
- #11 — Cleanup pós‑merge F‑10 (CI)
- #12 — Evidências F‑10 (PR)
- #15 — Ajustes correlatos ao fechamento da F‑10

## Known follow‑ups
- #13 — Cobertura Chromatic ≥ 95% por tenant (endurecer gate no PR)
- #14 — Budgets estritos de Lighthouse/k6 no PR

## Como publicar

Tag e push:
```bash
git tag -a v1.0 -m "F-10 Frontend Foundation (v1.0)"
git push origin v1.0
```

GitHub Release:
- Criar um Release no GitHub apontando para a tag `v1.0`.
- Usar este arquivo (`docs/RELEASE_NOTES_F10.md`) como release notes (copiar/colar ou anexar como referência).
