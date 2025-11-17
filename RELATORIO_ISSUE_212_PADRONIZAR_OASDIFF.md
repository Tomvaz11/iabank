# Relatório — Issue #212: Padronizar menções 'openapi-diff' → 'oasdiff'

Data: 2025-11-17
Responsável: Assistente (gh CLI)
Issue: https://github.com/Tomvaz11/iabank/issues/212
PR: https://github.com/Tomvaz11/iabank/pull/227

## Objetivo
Padronizar documentação e exemplos para a ferramenta atual `oasdiff`, substituindo menções legadas a `openapi-diff` quando aplicável.

## Ações Executadas
- Mapeamento de ocorrências:
  - Comando: `rg -n "openapi-diff" docs .github scripts contracts backend`.
  - Restaram apenas ocorrências em código/migrações do backend (choices do enum e históricos), mantidas por compatibilidade.
- Renomeio do wrapper de diff:
  - `contracts/scripts/openapi-diff.sh` → `contracts/scripts/oasdiff.sh` (mesma funcionalidade; usa `oasdiff breaking`).
- Atualizações em referências (docs/CI/scripts):
  - `.github/workflows/ci-contracts.yml`: step chama `contracts/scripts/oasdiff.sh`.
  - `package.json`: script `openapi:diff` atualizado para `contracts/scripts/oasdiff.sh`.
  - `docs/pipelines/ci-required-checks.md`: referência ao wrapper atualizada.
  - `CONTRIBUTING.md`: referências ao wrapper atualizadas (inclui nota do baseline por label).
  - `RELATORIO_ISSUE_181_MIGRACAO_OPENAPI31_OASDIFF.md`: links e exemplos corrigidos para `oasdiff.sh`.
  - `RELATORIO_ISSUE_214_BASELINE_31_SOMBRA.md`: referência ao wrapper ajustada.
  - `docs/runbooks/governanca-oasdiff-pin.md` e `docs/adr/013-governanca-pin-oasdiff.md`: apontam para `contracts/scripts/oasdiff.sh`.
  - `specs/002-f-10-fundacao/tasks.md`: tarefa inicial menciona o wrapper novo.

## Validações
- Busca final por menções legadas:
  - `rg -n "openapi-diff.sh"` → nenhuma ocorrência.
  - `rg -n "\bopenapi-diff\b" docs .github scripts contracts` → sem ocorrências.
  - Ocorrências remanescentes em `backend/` (models/migrations) são históricas e compatibilidade de dados; não afetam documentação/exemplos.

## Commits Relevantes
- 73bd0fd — chore(contracts): alinhar referências ao wrapper oasdiff.sh (renomeado)

## Sincronização e Fluxo de PR
- Branch criada: `fix/212-docs-oasdiff-padroniza`.
- Push realizado e PR aberto: #227.
- Auto‑merge habilitado (squash + delete branch).
- Branch local removida após abrir o PR.
- Após merge, a branch remota será removida automaticamente (auto‑merge configurado com `--delete-branch`).

## Decisões
- Não alterar `backend/apps/contracts/models.py` e migrações legadas com `openapi-diff` para preservar compatibilidade de dados e histórico.
- Padronizar apenas documentação, exemplos, workflows e scripts de automação.

## Pendências
- Aguardar conclusão dos checks do PR #227 (auto‑merge ativo). Nenhuma outra pendência técnica.

## Como validar rapidamente
- `pnpm openapi:lint` e `pnpm openapi:diff` (opcional) — garantem que scripts e wrappers continuam funcionais.
- `rg -n "openapi-diff" docs .github scripts contracts backend` — confirmar que apenas backend (choices/migrações) contém a string.
