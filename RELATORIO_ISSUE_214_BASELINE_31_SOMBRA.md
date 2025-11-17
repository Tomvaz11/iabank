# Relatório — Issue #214: CI/Contracts: Baseline 3.1 sombra (via label)

Data: 2025-11-17
PR: https://github.com/Tomvaz11/iabank/pull/224
Issue: https://github.com/Tomvaz11/iabank/issues/214

## Objetivo
Permitir dry‑run do baseline 3.1 sem promover `contracts/api.previous.yaml`, usando um baseline alternativo quando o PR tiver o label `contracts:baseline-3.1`.

## Ações Executadas
- Atualizado o wrapper de diff:
  - `contracts/scripts/oasdiff.sh` agora aceita `--baseline PATH` e a variável `OPENAPI_BASELINE`, com precedência: CLI > env > default (`contracts/api.previous.yaml`).
  - Loga explicitamente a origem e o caminho do baseline selecionado.
- Ajustado o workflow de contratos:
  - `.github/workflows/ci-contracts.yml` passa a usar o wrapper para o diff.
  - Adicionado step que detecta o label `contracts:baseline-3.1` e exporta `OPENAPI_BASELINE=contracts/api.baseline-3.1.yaml` via `$GITHUB_ENV`.
  - Step de changelog (`oasdiff changelog`) respeita o baseline selecionado.
- Adicionado baseline alternativo:
  - `contracts/api.baseline-3.1.yaml` (cópia do `contracts/api.yaml` atual).
- Documentação:
  - `docs/pipelines/ci-required-checks.md` — seção “Baseline 3.1 (sombra)”.
  - `docs/runbooks/governanca-api.md` — instruções de uso do label no PR.
- PR aberto e auto‑merge habilitado:
  - PR #224 criado com título convencional e tag `@SC-001`.
  - Label `contracts:baseline-3.1` aplicado ao PR para evidenciar o fluxo.
  - Auto‑merge habilitado com squash e remoção automática da branch após merge.

## Commits Relevantes
- b614a65 — ci(contracts): suporte a baseline 3.1 via label (sombra)

## Arquivos Alterados/Adicionados
- M `.github/workflows/ci-contracts.yml`
- M `contracts/scripts/oasdiff.sh`
- A `contracts/api.baseline-3.1.yaml`
- M `docs/pipelines/ci-required-checks.md`
- M `docs/runbooks/governanca-api.md`

## Decisões Tomadas
- Precedência do baseline alinhada ao pedido da issue (CLI > env > default).
- O workflow passou a chamar o wrapper para garantir logging consistente e respeitar o baseline via label.
- O label é lido apenas em PRs (`if: pull_request`). Sem label, comportamento permanece inalterado.

## Sincronização e Limpeza
- Branch criada: `ci/baseline-3.1-label-shadow` (removida localmente após abrir PR).
- Remoto atualizado: branch publicada e PR #224 aberto contra `main`.
- Auto‑merge habilitado (`--squash --delete-branch`). A exclusão da branch remota ocorrerá automaticamente após os checks.

## Pendências
- Merge do PR #224 depende da aprovação/checks do CI; auto‑merge está ativo. Não há outras pendências.

## Como Validar
- Em um PR com o label `contracts:baseline-3.1`, o log do job “OpenAPI diff (oasdiff breaking via script)” deve conter:
  - “Baseline selecionado (env): contracts/api.baseline-3.1.yaml”.
  - Execução do `oasdiff breaking <baseline 3.1> -> contracts/api.yaml`.
- Sem o label, o baseline padrão permanece: `contracts/api.previous.yaml`.
