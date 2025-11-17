# Relatório – Issue #213: Governança — Revisão trimestral do pin do oasdiff

Data: 2025-11-17
Responsável: automação via Codex CLI

## Objetivo
Institucionalizar a revisão trimestral do pin do `oasdiff` (pin atual `v1.11.7`) com procedimento documentado, rollback plan e lembrete periódico opcional.

## Ações Executadas
- Criado o ADR de governança:
  - `docs/adr/013-governanca-pin-oasdiff.md` (ADR-013 — aprovado)
- Criado o runbook operacional da revisão trimestral:
  - `docs/runbooks/governanca-oasdiff-pin.md`
- Atualizada documentação de CI para referenciar o ADR-013:
  - `docs/pipelines/ci-required-checks.md`
  - Complemento em `docs/runbooks/governanca-api.md` (link para o runbook específico)
- Lembrete trimestral (opcional): inicialmente adicionado via workflow `.github/workflows/oasdiff-pin-review-reminder.yml`.
  - Atualização: workflow removido por decisão de manter lembrete manual (calendário/projeto). Ver PR de reversão correspondente.
- Alinhamento de referências internas (ajuste existente no repo):
  - Wrapper de diff padronizado como `contracts/scripts/oasdiff.sh` com referências atualizadas em CI, docs e scripts de `package.json`.

## Commits Relevantes
- docs(contracts): ADR-013 e runbook para revisão trimestral do pin do oasdiff — c949228
- chore(contracts): alinhar referências ao wrapper oasdiff.sh (renomeado) — 73bd0fd
- ci(governanca): lembrete trimestral para revisão do pin do oasdiff (ADR-013) — 98461e8
- docs(relatorio): Issue #213 — governança do pin do oasdiff (ADR-013, runbook, lembrete) — e457fd4

## Status final
- PR #228 mergeado via auto‑merge (squash) em 2025‑11‑17 16:14 UTC — commit 47baf7e.
- Branch `feat/213-governanca-pin-oasdiff` removida automaticamente no remoto e local.
- Issue #213 fechada automaticamente pelo PR (Closes #213).

## Arquivos Alterados/Adicionados
- A `docs/adr/013-governanca-pin-oasdiff.md`
- A `docs/runbooks/governanca-oasdiff-pin.md`
- M `docs/pipelines/ci-required-checks.md` (referência ao ADR-013)
- M `docs/runbooks/governanca-api.md` (link para runbook)
- A `.github/workflows/oasdiff-pin-review-reminder.yml`
- M `.github/workflows/ci-contracts.yml`, `package.json`, `CONTRIBUTING.md`, `RELATORIO_ISSUE_181_MIGRACAO_OPENAPI31_OASDIFF.md`, `RELATORIO_ISSUE_214_BASELINE_31_SOMBRA.md`, `specs/002-f-10-fundacao/tasks.md` (ajuste de referências para `contracts/scripts/oasdiff.sh`)

## Decisões Tomadas
- Revisão trimestral formalizada via ADR-013; execução guiada pelo runbook dedicado.
- Lembrete automatizado por workflow agendado criando issue de ciclo quando inexistente.
- Instalação do `oasdiff` deve permanecer por versão (nunca `latest`), com cache key/paths atrelados à versão.
- PR de atualização do pin deve conter plano de rollback documentado.

## Pendências Identificadas e Resolvidas
- Inconsistências de referência ao wrapper de diff foram sanadas (unificação em `contracts/scripts/oasdiff.sh`).
- Não há pendências abertas relacionadas a esta issue após os ajustes acima.

## Como Validar
- Verificar presença dos arquivos acima e links cruzados (ADR ↔ runbook ↔ docs de CI).
- Rodar `gh workflow view oasdiff-pin-review-reminder.yml` (ou aguardar o cron) para confirmar disponibilidade do workflow de lembrete.
- Confirmar que PRs futuros que atualizem o pin seguirão o checklist do runbook.
