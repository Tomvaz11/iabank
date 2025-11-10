**Resumo — Issue #85: Timeouts em steps longos + artefatos do ZAP**

- Número/Título: #85 — CI: Timeouts em passos longos + artefatos do ZAP para troubleshooting
- Estado: FECHADA em 2025-11-10T01:30:22Z
- PR relacionado: #102 (ci/test/security): “Vitest 85% + ZAP artifacts (#81,#85)” — merge em main em 2025-11-10T01:24:55Z
- Confirmações no GitHub:
  - Comentário final da issue indica que os artefatos do ZAP e o resumo foram incorporados ao main via PR #102.
  - Execuções recentes do workflow principal mostram falhas em alguns jobs (não diretamente impeditivas para o objetivo da issue), e sucesso em outros workflows (“Vault Rotation Checks”).

**Escopo implementado no workflow**

- Workflow: `.github/workflows/frontend-foundation.yml`
- Timeouts adicionados em passos longos (exemplos):
  - Visual & Accessibility:
    - Build Storybook estático — `timeout-minutes: 15`.
    - Chromatic — `timeout-minutes: 20`.
    - Test-runner do Storybook (axe/WCAG) — `timeout-minutes: 15`.
  - Performance:
    - k6 smoke — `timeout-minutes: 5`.
    - Playwright + Lighthouse budgets — `timeout-minutes: 15`.
  - Security:
    - SAST (Semgrep) — `timeout-minutes: 10`.
    - DAST (OWASP ZAP baseline) — `timeout-minutes: 12` com upload de artefatos e resumo no Step Summary.
    - pip-audit — `timeout-minutes: 10`; Safety — `timeout-minutes: 10`.
    - pnpm audit — `timeout-minutes: 10`; SBOM (geração) — `timeout-minutes: 10`.
- Artefatos e resumo do ZAP:
  - Passo “Upload ZAP artifacts” publica `artifacts/zap` como artifact (`zap-reports`).
  - Passo “Resumo ZAP” escreve no `$GITHUB_STEP_SUMMARY` o outcome do DAST e o caminho dos artefatos.
- Script do DAST: `scripts/security/run_dast.sh`
  - Executa ZAP baseline contra `ZAP_BASELINE_TARGET` e salva relatórios em `artifacts/zap` (JSON/HTML/XML/MD).

**Observações**

- A implementação atende ao objetivo da issue (timeouts nos steps críticos e publicação de artefatos/resumo do ZAP).
- Alguns passos de instalação/execução gerais (ex.: “Install dependencies” e execução do Vitest) não possuem `timeout-minutes` explícito; se desejado, pode-se endurecer adicionando limites também nesses pontos.

**Como Validar na Prática**

- Objetivo 1 — Artefatos e resumo do ZAP são publicados:
  - Dispare manualmente o workflow via `workflow_dispatch` (ou abra um PR) e aguarde a execução do job “Security Checks”.
  - Verifique na aba “Summary” do job a linha com “DAST outcome: …; Artifacts: artifacts/zap”.
  - Baixe o artifact `zap-reports` e confirme a presença dos arquivos (ex.: `zap-baseline.json`, `zap-warnings.md`, `zap-report.html`, `zap-report.xml`).

- Objetivo 2 — Timeouts ativam em passos longos:
  - Crie uma branch de teste (ex.: `test/issue-85-timeouts`) e, temporariamente, insira `sleep 1200` no início de um passo com timeout (ex.: “Playwright + Lighthouse budgets” que tem `timeout-minutes: 15`).
  - Abra um PR e aguarde o job correspondente: o step deve falhar por “timed out” em ~15 minutos.
  - Reverta o `sleep` após a verificação.

- Objetivo 3 — Caminho feliz com DAST e artefatos:
  - Em `main` (ou PR com mudanças em `backend/**` ou `scripts/security/**`), execute o workflow sem injeções artificiais.
  - Confirme que o job “Security Checks” roda o DAST, publica os artefatos e escreve o resumo, e que o pipeline reflete corretamente o resultado (fail-closed em `main/releases/tags` quando configurado, ou conforme as flags `CI_ENFORCE_FULL_SECURITY`/`CI_FAIL_OPEN`).

**Checklist de Validação**

- [ ] Artifact `zap-reports` presente com relatórios completos.
- [ ] Summary do job contém o bloco do “Resumo ZAP” com outcome e caminho dos artefatos.
- [ ] Simulação de step longo resulta em “timed out” dentro do tempo configurado.
- [ ] Execução “caminho feliz” passa sem pendurar steps longos (sem loops indefinidos).

