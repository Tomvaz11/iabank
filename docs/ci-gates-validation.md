# Validação dos Gates de CI — Anotações de PR pelo Outage Guard (NFR-008)

Contexto
- Issue #82: permitir anotar PRs (labels/comentários) a partir do Outage Guard.
- PR #90 aplicou `permissions` no workflow principal para habilitar escrita em PRs.

Permissões exigidas (GITHUB_TOKEN)
- No workflow `.github/workflows/frontend-foundation.yml`, garantir:
  - `permissions:`
    - `contents: read`
    - `pull-requests: write`
    - `issues: write`

Como validamos (smoke test)
- Adicionamos um workflow temporário `ci-smoke-pr-annotations.yml` (workflow_dispatch) para postar um comentário e aplicar/remover uma label em um PR existente, usando `GITHUB_TOKEN`.
- Executamos na branch `main` com `pr_number=90`.
- Logs do run confirmaram:
  - comentário criado e removido com sucesso;
  - label temporária adicionada e removida com sucesso.

Evidências
- PR de permissão: PR #90 — “ci(outage): permissões para anotar PRs (#82)”.
- Run de smoke na main: Actions run `PR Annotations Smoke Test` (success) — URL: ver histórico de Actions em `main` na data 2025‑11‑09 (run `19215914570`).
- Limpeza do workflow/label de teste:
  - PR #95 — remove `ci-smoke-pr-annotations.yml` (mergeado).
  - Label `ci-smoke-annotations` removida do repositório.

Operação
- O Outage Guard (job `ci-outage-guard`) só anotará PRs quando detectar outage; em runs normais (`outages: []`), nada será escrito.
- Em caso de ajuste futuro, repetir o smoke test acima para garantir o caminho de escrita.

