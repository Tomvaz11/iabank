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
- CI Outage Guard: fail‑open em branches não release para ferramentas de QA; fail‑closed em `main`/`release/*`/`hotfix/*`.

### Referências rápidas de CI/Workflows
- Workflow principal: `.github/workflows/frontend-foundation.yml:1`
- Inspecionar runs (gh CLI):
  - `gh run list --limit 10`
  - `gh run view <RUN_ID>` (ou somente falhas: `--log-failed`)
  - `gh run rerun <RUN_ID>` (ou `--failed` para reexecutar só o que falhou)
- Gates típicos por evento:
  - Vitest branches: PR ≥ 84.5%, main/releases ≥ 84.8%
  - Segurança: fail‑closed em main/releases; fail‑open em PR/dev
  - Performance budgets: “hard” em main; “soft” em PR

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

## Governança (resumo)
- Revisões: CODEOWNERS define responsáveis por áreas do código.
- Proteção da `main`: habilite no GitHub (require PR, squash only, linear history, required checks). Configuração é feita nas “Branch protection rules” do repositório.
- Aprovações obrigatórias: enquanto houver 1 mantenedor, mantenha 0 aprovações obrigatórias (evita bloqueios). Ao formar equipe, passe para 1–2 aprovações e, se fizer sentido, exija review de CODEOWNERS.

Se tiver dúvidas, abra um PR rascunho (draft) e marque as seções pendentes no template.
