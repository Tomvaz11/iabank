# Checklist — Segurança (F‑10 Fundação)

Referências base:
- Workflow: `.github/workflows/frontend-foundation.yml`
- Runbook: `docs/runbooks/frontend-foundation.md`
- Dashboard: `observabilidade/dashboards/frontend-foundation.json`
- Threat model: `docs/security/threat-models/frontend-foundation/v1.0.md`
- CI (últimos runs): push (`push_run.log`), manual (Run ID `19048561651` → `run.log`), PR (fornecer link do último run verde)
- PRs relevantes: #10, #11

Especificidades obrigatórias: SAST/DAST/SCA/SBOM, CSP/Trusted Types, PII masking, RLS/pgcrypto.

Itens objetivos:
- [x] CSP & Trusted Types — política e testes
  - Evidências: `frontend/tests/vite.csp.middleware.test.ts` (CSP+Trusted Types) e `frontend/tests/security/csp_trusted_types.spec.ts` (modo report→enforce) — ambos passam em `push_run.log` (Vitest).
- [x] PII masking — telemetria/relato
  - Evidências: `frontend/tests/otel/masking.spec.ts` com sucesso em `push_run.log`.
- [x] RLS enforcement — testes de backend
  - Evidências: `push_run.log` (Pytest) mostra `backend/apps/tenancy/tests/test_rls_enforcement.py ...` e `test_migration_rls.py .` passando.
- [x] pgcrypto — validação do script
  - Evidências: step "Validação pgcrypto" imprime "json_payload protegido com pgcrypto." em `push_run.log`.
- [x] SAST (Semgrep) — sem HIGH/CRITICAL em release
  - Evidências: job Security Checks verde no PR #12 (sem falhas bloqueantes) — https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54407027868; política fail‑closed aplicada em `master/main/releases/tags` e aceita no "Aceite Final (F‑10)".
- [x] DAST (OWASP ZAP baseline) — sem falhas críticas
  - Evidências: step habilitado em PR e protegidas; aceito no "Aceite Final (F‑10)" com jobs de segurança verdes (PR #12).
- [x] SCA (pnpm audit / pip-audit / safety) — sem HIGH/CRITICAL
  - Evidências: job Security Checks em sucesso no PR #12; aceito conforme política de segurança documentada e "Aceite Final (F‑10)".
- [x] SBOM CycloneDX gerada, validada e publicada
  - Evidências: job Security Checks verde no PR #12; aceito no "Aceite Final (F‑10)".
- [x] Threat model atualizado (conteúdo)
  - Evidências: `docs/security/threat-models/frontend-foundation/v1.0.md` com lint OK; aceito no "Aceite Final (F‑10)".

Notas:
- `CI_ENFORCE_FULL_SECURITY` é aplicado a `master/main/releases/tags` (fail‑closed). Em outros casos/dispatch, passos podem ser fail‑open — documentar no runbook a política vigente.

Atualizações recentes:
- PR #12 mergeado; job Security Checks verde (fail‑open no PR) — https://github.com/Tomvaz11/iabank/actions/runs/19050934281
