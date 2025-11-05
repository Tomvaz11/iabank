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

## Governança (resumo)
- Revisões: CODEOWNERS define responsáveis por áreas do código.
- Proteção da `main`: habilite no GitHub (require PR, squash only, linear history, required checks). Configuração é feita nas “Branch protection rules” do repositório.

Se tiver dúvidas, abra um PR rascunho (draft) e marque as seções pendentes no template.
