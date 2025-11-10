# Issue #82 — CI: Permitir anotar PRs no outage guard (issues: write)

## Resumo do estado atual
- Status: CLOSED
- Link: https://github.com/Tomvaz11/iabank/issues/82
- Implementação: PR #90 — ci(outage): permissões para anotar PRs (#82)
  - Link: https://github.com/Tomvaz11/iabank/pull/90
  - Merge: 2025-11-09T21:28:38Z (branch `issue-82-ci-outage-perms` → `main`)
  - Alteração principal: `.github/workflows/frontend-foundation.yml` com `permissions: contents: read; pull-requests: write; issues: write`.
  - Job responsável: `ci-outage-guard` (executa `node scripts/dist/ci/handle-outage.js`).
- Evidência de validação (smoke/E2E):
  - GitHub Actions “PR Annotations Smoke Test” — Run `19215914570` — conclusão: success
  - Link: https://github.com/Tomvaz11/iabank/actions/runs/19215914570
  - Resultado: comentário e label aplicados/removidos com sucesso no PR #90 (fail‑open fora de release).
- Limpeza: PR #95 — remove workflow temporário de smoke de anotações
  - Link: https://github.com/Tomvaz11/iabank/pull/95 — MERGED em 2025-11-09T23:39:22Z
  - Ação: remoção do workflow de smoke; label de teste `ci-smoke-annotations` removida do repositório.
- Documentação: PR #96 — docs(ci): validar gates e registrar permissões do Outage Guard
  - Link: https://github.com/Tomvaz11/iabank/pull/96 — MERGED em 2025-11-10T00:02:10Z

Arquivos relevantes no repositório:
- Workflow: `.github/workflows/frontend-foundation.yml` (contém o job `ci-outage-guard`).
- Script: `scripts/ci/handle-outage.ts` (gera evento OTEL, aplica label `ci-outage` e comenta em PRs no modo fail‑open; falha pipeline no modo fail‑closed).
- Self-test auxiliar: `.github/workflows/ci-outage-selftest.yml` (simula conditions de outage para observabilidade; não substitui o teste de anotação em PR).

---

## Como validar na prática (E2E)
Objetivo: comprovar que, diante de falha de Chromatic/Lighthouse/Axe, o job `ci-outage-guard` aplica comentário e label `ci-outage` em PRs de branches não‑release (fail‑open) e falha o pipeline em `main`/`release/*` (fail‑closed).

Passos recomendados:
1) Preparar PR(s) de teste
- Criar um PR a partir de uma branch interna (ex.: `feature/ci-outage-validation`) contra `main`.
- Opcional: criar outro PR a partir de um fork para observar restrições de token em forks.

2) Induzir um outage controlado (qualquer um dos abaixo)
- Visual & Accessibility (`visual-accessibility`): provocar falha no trecho de Chromatic/axe (ex.: usar token Chromatic inválido temporariamente ou ajustar um step para retornar `exit 1`).
- Performance (`performance`): provocar falha em Lighthouse/Playwright (ex.: budget propositalmente impossível ou `exit 1` controlado).
- Observação: reverta qualquer alteração/secret após o teste.

3) Executar o CI
- O workflow alvo é “Frontend Foundation CI” (`.github/workflows/frontend-foundation.yml`).
- Dispare via push/PR ou manualmente por `workflow_dispatch` (sem inputs).

4) Verificar comportamento em PR não‑release (fail‑open)
- No PR: deve surgir a label `ci-outage` e um comentário com resumo do outage.
- O pipeline deve concluir sem falhar por conta do outage (demais gates mantêm sua própria política).
- Reexecutar após remover a causa da falha e confirmar que o comentário não se duplica (idempotência) e que a label pode ser removida (manual, conforme instrução do comentário) quando tudo voltar a verde.

5) Verificar comportamento em `main`/`release/*` (fail‑closed)
- Repetir o teste direcionando a base para `main` ou abrindo PR para `release/*`.
- Esperado: `ci-outage-guard` finalize com erro e o workflow falhe (sem aplicar política fail‑open).

6) Caso de PR de fork (opcional, segurança)
- Em PRs de forks, o token padrão costuma ser read‑only; é esperado que a tentativa de rotular/comentar resulte em aviso no log e não em falha do job (graceful degradation).

7) Observabilidade e auditoria
- Conferir logs do job `ci-outage-guard` e, se configurado, o artefato/arquivo `observabilidade/data/ci-outages.json` e eventos OTEL/Sentry.
- Validar que permissões de escrita em `pull-requests`/`issues` estão ativas e funcionando para o job de anotação.

Critérios de aceitação
- Label `ci-outage` e comentário aplicados em PRs não‑release quando houver falha nas ferramentas citadas; pipeline não quebra por isso.
- Em `main`/`release/*`, o pipeline quebra (fail‑closed) na presença de outage.
- Comportamento idempotente (sem spam de comentários/labels) e logs claros.
- Evidências coletadas: links de PRs e runs do Actions anexados às docs do projeto.

## Evidências da validação executada agora
- PR de teste: #115 — https://github.com/Tomvaz11/iabank/pull/115 (branch `chore/ci-pr-annotation-smoke-issue-82`)
- Run (fail-open, com anotação no PR): https://github.com/Tomvaz11/iabank/actions/runs/19242247663
  - Resultado visível no PR: label `ci-outage` aplicada e comentário criado.
- Run adicional (fail-closed, simulado em `main`): https://github.com/Tomvaz11/iabank/actions/runs/19242295777
  - Objetivo: validar caminho de fail-closed (sem anotar PR). O job é tolerante a erro (`continue-on-error`) apenas para fins de selftest.
