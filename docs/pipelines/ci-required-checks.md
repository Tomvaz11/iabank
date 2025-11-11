# Pipeline: CI Required Checks

Reflete os gates constitucionais (v5.2.0) e ADRs 008–012.

## Jobs Obrigatórios
1. **tests-unit**: `pytest` (preferencialmente sharded com `xdist`), cobertura ≥85%.
2. **tests-integration**: inclui cenários de RLS (`CREATE POLICY` + enforcement) e `factory-boy`.
3. **tests-contract**: Spectral, openapi-diff, Pact (`ci/contracts.yml`) com cenários de idempotência e concorrência.
4. **tests-security**: SAST, DAST, SCA, verificação de pgcrypto/mascaramento (scripts do ADR-010).
5. **tests-performance**: k6 com thresholds definidos nos SLOs aprovados (documentar no repositório de SLOs/SLA) e revisados semestralmente.
6. **build-sbom**: Gera CycloneDX/SPDX.
7. **iac-policy**: Terraform plan + OPA/Gatekeeper.
8. **finops-tags**: Script para validar tagging obrigatório (Artigo XVI).
9. **complexity-gate**: Radon cc ≤ 10 (Python) usando `scripts/ci/check_python_complexity.py` e allowlist controlado.

## Automação Pendente
- Revisar periodicamente os scripts em `scripts/` conforme o amadurecimento dos serviços.
- Ajustar workflows (`.github/workflows/*.yml`) quando a infraestrutura real for integrada.
- Atualizar o catálogo de SLO/thresholds em `docs/slo/` sempre que novos domínios surgirem.

## Estratégia de Execução
- Habilitar paralelização (e.g., `pytest-xdist`, `k6` em múltiplos VUs) para manter SLAs de pipeline < 15 min.
- Usar filtros de caminho/monorepo para executar somente jobs impactados por cada PR.
- Monitorar tempos de execução e ajustar limites de cobertura/thresholds via ADR antes de qualquer alteração.
- Registrar métricas de sucesso dos jobs para alimentar dashboards DORA/SLO automaticamente.

## Otimizações de CI (2025-11-08)
- Step-gating por paths mantendo os jobs required sempre presentes:
  - Visual & Accessibility e Performance só executam build/Chromatic/Playwright/k6/Lighthouse quando há mudanças de UI (`frontend/**`, Storybook, lockfiles e workspace).
  - Contracts (Spectral/OpenAPI diff/Pact) só executam quando há mudanças em `contracts/**`.
  - Security (Semgrep, ZAP, pip-audit, Safety, SBOM) executa quando há mudanças em `backend/**`, `frontend/**` ou `scripts/security/**`; em `main/releases/tags` permanece fail-closed e forçado.
- Concurrency/cancel-in-progress habilitado no workflow principal (por workflow + ref/PR).
- Playwright padronizado para Chromium nos jobs relevantes (reduz tempo e intermitências de dependências do SO).
- Caches adicionados: `actions/cache` para `~/.cache/pypoetry` e `~/.cache/pip`; cache PNPM já via `setup-node`.
- Timeouts defensivos aplicados a passos pesados (Chromatic, Storybook test, k6/Lighthouse, Semgrep/ZAP/SCA).
- Artifacts com `retention-days` (Chromatic e Performance: 7–14 dias; SBOM: 30 dias).

Nota operacional: esta seção foi ajustada apenas para validar o comportamento de gating em um PR "docs-only".

## Atualizações (2025-11-11) — Lote 2
- Pre-commit incremental por diff (PR):
  - `actions/checkout@v4` com `fetch-depth: 0` para garantir histórico e permitir `--from-ref/--to-ref`.
  - PRs executam `pre-commit run --from-ref $BASE --to-ref $HEAD --show-diff-on-failure`.
  - Em `main`/`release/*`/tags, executa `--all-files`.
## Atualizações (2025-11-11) — Lote 3
- Testes paralelos: dividido em dois jobs — `test-frontend` (Vitest) e `test-backend` (Pytest + Radon), ambos com `needs: [lint, changes]` e execução paralela.
- Gates por paths nos testes:
  - Vitest: executa quando `needs.changes.outputs.frontend == 'true'` (PR/dev) e SEMPRE em `main`/`release/*`/tags.
  - Pytest + Radon: executa quando `needs.changes.outputs.backend == 'true'` (PR/dev) e SEMPRE em `main`/`release/*`/tags.
- Contracts:
  - `contracts` não depende mais de `test`.
  - Pact consumer verification roda quando `contracts == 'true'` OU `frontend == 'true'`.
  - Spectral/OpenAPI diff roda apenas quando `contracts == 'true'`.

## Atualizações (2025-11-11) — Lote 4
- Timeouts por job (frontend-foundation):
  - Performance Budgets: `timeout-minutes: 30` no nível do job.
  - Security Checks: `timeout-minutes: 25` no nível do job.
- Timeouts existentes em steps foram preservados (Chromatic, Storybook test, k6/Lighthouse, Semgrep/ZAP/SCA etc.).
- Arquivo de referência: `.github/workflows/frontend-foundation.yml`.

## Prova de TDD (Art. III)
- PRs DEVEM evidenciar “vermelho → verde” para mudanças de código:
  - Inclua no corpo do PR os commits/links para: (1) estado vermelho (testes falhando) e (2) estado verde (após implementação).
  - Alternativamente, anexe logs do job ‘test’ que mostrem a falha esperada anterior à correção.
- Exceções pontuais (hotfix de infraestrutura, ajustes em scripts/CI ou documentação) DEVEM registrar justificativa no PR.

## Complexidade (Radon)
- O job `Radon complexity gate` no workflow `frontend-foundation.yml` executa `scripts/ci/check_python_complexity.py` (limite cc ≤ 10; allowlist em `scripts/ci/complexity_allowlist.json`).
- Localmente, rode: `poetry run python scripts/ci/check_python_complexity.py`.

## Saídas
- Artefatos devem ser enviados para armazenamento WORM.
- Resultados agregados alimentam os dashboards DORA/SLO.

## Contextos de proteção (GitHub Required Checks)
Estes são os contextos atualmente exigidos na proteção da branch `main` (Branch protection rules). Mantemos a lista aqui para referência rápida e auditoria:
- Lint
- Vitest
- Pytest + Radon
- Contracts (Spectral, OpenAPI Diff, Pact)
- Visual & Accessibility Gates
- Performance Budgets
- Security Checks
- Threat Model Lint
- CI Outage Guard
- CI Diagnostics
- Validate Renovate configuration

Nota — CI Outage Guard (permissões para anotar PR)
- Para que o Outage Guard possa rotular/comentar PRs quando houver outage, o workflow principal precisa do bloco `permissions` com:
  - `contents: read`
  - `pull-requests: write`
  - `issues: write`
- Este requisito foi aplicado no PR #90 e verificado em 2025‑11‑09 via smoke test (comentário/label criados e removidos com sucesso em PR existente).

Notas de governança relacionadas:
- Merge: squash-only, com exclusão de branch ao mesclar.
- Histórico linear: habilitado.
- Resolução de conversas antes do merge: habilitada.
- Aprovações obrigatórias: 0 (atual) — quando houver equipe, migrar para 1–2 aprovações e, se desejado, exigir review de CODEOWNERS.

## Notas SAST (Semgrep)
- Script: `scripts/security/run_sast.sh`.
- Timeout: `--timeout ${SEMGREP_TIMEOUT:-300}` — por padrão o scan é interrompido após 300s para evitar travas.
- Como ajustar: defina `SEMGREP_TIMEOUT` no ambiente do workflow (ex.: `env: SEMGREP_TIMEOUT: 600`) para alterar o limite.
- Métricas/version-check: desabilitados no script (`--metrics=off`, `--disable-version-check`) para execução determinística no CI.

## Notas DAST (ZAP)
- Alvo do DAST: `http://127.0.0.1:8000/metrics` (exposto por `django_prometheus`).
- O job provisiona Postgres (`services: postgres:15`) e exporta `FOUNDATION_DB_*` para o Django conectar.
- O script `scripts/security/run_dast.sh` aplica migrações e inicia o `runserver` antes do scan; aguarda o endpoint responder.
- Política (atualizada em 2025‑11‑08): em PRs, `main`, `release/*` e tags é fail‑closed (sem `fail‑open`). Em `workflow_dispatch`, segue política de sanidade do workflow.
  - Tratamento de severidade: WARN não quebra pipeline (exit 2 do ZAP é normalizado para sucesso); FAIL quebra (exit 1/3) — reduz ruído mantendo fail‑closed para vulnerabilidades reais.
 - Artefatos publicados (artifact `zap-reports`):
   - `zap-baseline.json` (JSON do baseline)
   - `zap-report.html` (relatório navegável)
   - `zap-report.xml` (máquina/CI)
   - `zap-warnings.md` (resumo textual de avisos)
   - `django-zap.log` (log do backend durante o scan)
 - Resumo no Job Summary: o workflow grava no `$GITHUB_STEP_SUMMARY` a linha com o outcome do DAST e o caminho dos artefatos ("Artifacts: artifacts/zap").

## Notas SCA (Python)
- Ferramentas: `pip-audit` e `Safety` executam no job “Security Checks”.
- Feed online do Safety (3.x): habilitado via secret `SAFETY_API_KEY` do repositório.
  - O workflow principal injeta `SAFETY_API_KEY` no passo "Safety (Python SCA)".
  - O script `scripts/security/run_python_sca.sh` alterna automaticamente para `safety scan` (3.x) quando a variável está definida; sem a variável, faz fallback seguro para `safety check` (2.3.x, offline).
- Artefatos: `artifacts/python-sca/safety.json` e `artifacts/python-sca/pip-audit.json`.
- Política: em PRs e `main` é fail‑closed para High/Critical reportados pelo Safety; em branches não release fora de PR pode aplicar `CI_FAIL_OPEN` conforme política do workflow.

## Rotação do SAFETY_API_KEY (CI)
- Periodicidade recomendada: a cada 6 meses ou a qualquer sinal de comprometimento.
- Procedimento de rotação (GitHub Actions → Secrets do repositório):
  1. Gere uma nova chave no provedor do Safety (conta/console do Safety CLI).
  2. No repositório, acesse: Settings → Secrets and variables → Actions.
  3. Localize o secret `SAFETY_API_KEY` e clique em “Update secret”.
  4. Substitua pelo novo valor e salve.
  5. Valide com um PR trivial (ex.: alteração em docs) ou `workflow_dispatch` do workflow principal; o passo “Safety (Python SCA)” deve rodar com sucesso.
  6. Revogue a chave antiga no provedor do Safety.
- Observações:
  - Não registre a chave em issues/PRs/logs. Evite `set -x` em scripts que imprimam variáveis.
  - A substituição é imediata para novos jobs; jobs já em execução continuarão com o token que receberam no início da execução.
