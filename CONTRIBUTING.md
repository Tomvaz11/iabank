# Contribuindo para o IABANK (Fundação)

Este guia consolida o fluxo Git e as práticas de contribuição adotadas no repositório, alinhadas ao Spec‑Kit e aos gates do nosso CI.

## Padrão de Branch
- Preferencial (Spec‑Kit): `NNN-nome-da-feature` (ex.: `001-contas-listar`).
- Tolerado: `feature/**`, `fix/**`, `chore/**` (mantidos para flexibilidade).
- Sempre crie sua branch a partir de `main` atualizada: `git switch main && git pull --rebase && git switch -c 001-minha-feature`.

## Commits e PRs
- Mensagens: use Conventional Commits (ex.: `feat(ui): título curto e claro`).
- Squash merge: preferido em PRs para manter histórico linear e limpo.
- Evidências de TDD (obrigatórias no PR):
  - Link/commit do estado VERMELHO (teste falhando esperado) e do VERDE (após correção).
  - Exceções (infra/CI/docs) devem justificar no PR template.
- Tags Spec‑Kit: mencione pelo menos uma `@SC-00x` no título ou corpo do PR (validado pelo CI).
- Atualize a branch antes de abrir PR: `git fetch origin && git rebase origin/main` (ou `merge`).
- Evite `--force`; quando necessário, use `--force-with-lease` somente na sua branch de trabalho.

## Checks obrigatórios (CI)
A pipeline principal executa e/ou exige:
- Lint (ESLint, boundaries FSD).
- Testes (Vitest no frontend, Pytest no backend; cobertura mínima definida).
- Contratos (Spectral + openapi-diff + Pact).
- Visual/Acessibilidade (Storybook Test Runner + Chromatic) quando aplicável.
- Performance (k6 + Lighthouse budgets) quando aplicável.
- Segurança (SAST/DAST/SCA, pgcrypto, SBOM) com enforcement estrito em `main`/release.
- Threat model lint.
- Verificação de documentação: falha PR quando há mudanças impactantes (CI/infra/versions/contracts)
  sem atualização correspondente em `README.md`/`CONTRIBUTING.md`/`docs/`. Também verifica drift
  básico das versões (Node de `.nvmrc`, Poetry pinado no workflow e Python do `pyproject.toml`) contra o README.
- CI Outage Guard: fail‑open em branches não release para ferramentas de QA; fail‑closed em `main`/`release/*`/`hotfix/*`.
- Pre-commit (lint hooks):
  - Em PRs: execução incremental por diff entre base e head (`--from-ref $BASE --to-ref $HEAD`).
  - Em `main`/`release/*`/tags: execução full (`--all-files`).
  - O checkout do job usa `fetch-depth: 0` para garantir diffs confiáveis.
  - Hooks definidos em `.pre-commit-config.yaml` (ESLint/Ruff); o job grava um resumo no Job Summary.

### CI: Gating de jobs e uploads
- Jobs obrigatórios pela proteção de branch NÃO devem ser pulados no nível do job. Mantenha o gating por paths/refs no nível dos steps para preservar a presença dos checks (status “verde” quando não há trabalho).
- Para uploads, evite ruído de “No files were found…” usando `if-no-files-found: ignore` e/ou condicionais com `hashFiles()` (ex.: `if: ${{ always() && hashFiles('artifacts/pytest/**') != '' }}`).
- Segurança: reforçamos caches (Poetry/pip/pnpm e Semgrep) para reduzir tempo, mantendo execução completa em `main`/tags e execução limitada a paths relevantes em PRs.

- Testes (gates por paths) — Lote 3:
  - “Vitest” (job `test-frontend`): prepara Node e executa Vitest quando `needs.changes.outputs.frontend == 'true'` (em PR/dev). Em `main`/`release/*`/tags, sempre executa.
  - “Pytest + Radon” (job `test-backend`): prepara Python/Poetry e executa Pytest/Radon quando `needs.changes.outputs.backend == 'true'` OU `needs.changes.outputs.tests == 'true'` (em PR/dev). Em `main`/`release/*`/tags, sempre executa.
  - Dica: os passos “Resumo de mudanças (tests - frontend/backend/tests)” imprimem `needs.changes.outputs.frontend/backend/tests` para diagnóstico rápido.
  - Required checks: na branch `main`, “Vitest” e “Pytest + Radon” estão configurados como Required Checks (use o nome exato do job). Mantenha-os ao ajustar as Branch Protection Rules.

### Onde consultar gates do CI (sem duplicar valores)
- Workflow principal: `.github/workflows/frontend-foundation.yml:1`
- Como localizar regras no YAML:
  - Vitest (coverage gate): procurar `FOUNDATION_COVERAGE_BRANCHES` e os passos "Run Vitest (coverage gate)".
    - Comando: `rg -n "FOUNDATION_COVERAGE_BRANCHES|Run Vitest" .github/workflows/frontend-foundation.yml`
  - Segurança (fail-open/closed): procurar `CI_ENFORCE_FULL_SECURITY` e `CI_FAIL_OPEN`.
    - Comando: `rg -n "CI_ENFORCE_FULL_SECURITY|CI_FAIL_OPEN" .github/workflows/frontend-foundation.yml`
  - Performance (Lighthouse/k6): procurar "Performance Budgets" e "Lighthouse".
    - Comando: `rg -n "Performance Budgets|Lighthouse" .github/workflows/frontend-foundation.yml`
- Inspecionar runs no GitHub Actions (gh CLI):
  - `gh run list --limit 10`
  - `gh run view <RUN_ID>` (ou apenas falhas: `--log-failed`)
  - `gh run rerun <RUN_ID>` (ou `--failed` para só os jobs que falharam)

### Diagnóstico rápido (Lote 2)
- Pre-commit incremental (PR):
  - `gh run view <RUN_ID> --log | rg "Executando pre-commit por diff"`
- Gates por paths em testes:
  - PR frontend-only: `rg -n "pnpm test:coverage" artifacts && rg -n "poetry run pytest" artifacts` (espera “Vitest sim / Pytest não”).
  - PR backend-only: inverso do acima (espera “Pytest sim / Vitest não”).
  - `main`/`release/*`/tags: ambos executam.

## Runbooks úteis
- Outage (Chromatic/Lighthouse/Axe): `docs/runbooks/frontend-outage.md`.
- Renovate Validation (Node 22.13 no job; `renovate-config-validator`): `docs/runbooks/renovate-validation.md`.
- Vault/PII (pgcrypto, rotação e mascaramento): `docs/runbooks/seguranca-pii-vault.md`.

## Renovate
- Config: `renovate.json` (migrada para `matchFileNames`, `minimumReleaseAge` e `schedule` em entradas separadas).
- Validação no CI: workflow `renovate-validation.yml` com Node `22.13.0` e `--strict`.

## Dicas práticas
- Use `git add -p` para commits pequenos e focados.
- `git commit --fixup` + `git rebase -i --autosquash` para organizar antes do PR.
- `git stash -u` para pausar trabalho; `git reflog` para recuperar histórico.

## Pre-commit (hooks)
- Arquivo de configuração: `.pre-commit-config.yaml` (hooks: Ruff/Python, ESLint/Frontend e verificação de mensagem convencional).
- Ative localmente os hooks para “amarrar” o padrão antes do CI:
  - Com Poetry: `poetry run pre-commit install` (ou `pre-commit install`).
  - Rodar em todos os arquivos: `pre-commit run -a`.

## Ambiente Python/Poetry
- Versão padronizada: Poetry 1.8.3 (alinhado ao CI e ao Dockerfile).
- Instalação recomendada local:
  - `python -m pip install -U pip && pip install "poetry==1.8.3"`
  - `poetry install --with dev --sync --no-interaction --no-ansi`
  - O `poetry.lock` não deve ser recriado/alterado no CI; evite `poetry lock` em pipelines.

## Governança (resumo)
- Revisões: CODEOWNERS define responsáveis por áreas do código.
- Proteção da `main`: habilite no GitHub (require PR, squash only, linear history, required checks). Configuração é feita nas “Branch protection rules” do repositório.
- Aprovações obrigatórias: enquanto houver 1 mantenedor, mantenha 0 aprovações obrigatórias (evita bloqueios). Ao formar equipe, passe para 1–2 aprovações e, se fizer sentido, exija review de CODEOWNERS.

Se tiver dúvidas, abra um PR rascunho (draft) e marque as seções pendentes no template.
