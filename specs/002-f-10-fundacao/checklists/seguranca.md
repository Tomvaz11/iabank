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
- [ ] SAST (Semgrep) — sem HIGH/CRITICAL em release
  - Evidências (PR #12): job Security Checks verde (fail-open em PR) — https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54407027868
  - Observação: em runs anteriores há erro de schema ("Invalid rule schema" em `scripts/security/semgrep.yml`).
  - O que falta: correção das regras e link do step SAST com saída verde (0 HIGH/CRITICAL) no último run verde (push/PR) do workflow.
- [ ] DAST (OWASP ZAP baseline) — sem falhas críticas
  - Evidências: step definido para PR e branches protegidas.
  - O que falta: link do run de PR com step DAST concluído e relatório sem falhas críticas.
- [ ] SCA (pnpm audit / pip-audit / safety) — sem HIGH/CRITICAL
  - Evidências parciais: `pnpm audit` retorna 0 vulnerabilidades (push); `pip-audit` falhou ("The requested command export does not exist").
  - O que falta: link dos steps SCA (Node+Python) com sucesso e, se necessário, correção do pipeline Python (pip‑audit/safety) mostrando 0 HIGH/CRITICAL.
- [ ] SBOM CycloneDX gerada, validada e publicada
  - Evidências: step "Gerar SBOM" executa; `push_run.log` indica "SBOM não encontrada" na validação.
  - O que falta: artefato `sbom/frontend-foundation.json` gerado e validado (link do step "Upload SBOM" com sucesso).
- [ ] Threat model atualizado (conteúdo)
  - Evidências parciais: lint OK (ver `push_run.log`), arquivo `docs/security/threat-models/frontend-foundation/v1.0.md` presente.
  - O que falta: diff/PR com atualização pós‑validação (incluir CSP/Trusted Types/PII e decisões) e link do job "Threat Model Lint" verde do último run.

Notas:
- `CI_ENFORCE_FULL_SECURITY` é aplicado a `master/main/releases/tags` (fail‑closed). Em outros casos/dispatch, passos podem ser fail‑open — documentar no runbook a política vigente.
