# Resumo — Issue #83

Assunto: CI — Alinhar Poetry (CI e Docker) e remover `poetry lock` no CI

Estado geral
- Status: CONCLUÍDA (CLOSED em 2025-11-10T01:30:23Z)
- Implementação: via PR #105 (MERGED em 2025-11-10T01:29:53Z)
- Autor: @Tomvaz11 | Assignees: — | Labels: — | Milestone: —
- Link da issue: https://github.com/Tomvaz11/iabank/issues/83
- Link do PR: https://github.com/Tomvaz11/iabank/pull/105

O que foi feito
- Padronização da versão do Poetry para 1.8.3 no CI e no Docker.
- Remoção do passo `poetry lock --no-update` do workflow principal.
- No Dockerfile, `POETRY_VERSION=1.8.3` está configurado e a instalação usa `poetry install --with dev --no-ansi --no-interaction`.
- No workflow principal, a instalação Python usa `poetry install --with dev --no-ansi --no-interaction` (sem recriar o lock).

Evidências (alto nível)
- Comentário de encerramento na issue: “Alinhamento do Poetry e remoção de 'poetry lock' no CI mesclados via PR #105.”
- Actions (últimos runs relevantes):
  - Branch do PR: Frontend Foundation CI → failure
    - https://github.com/Tomvaz11/iabank/actions/runs/19217797022
  - Merge em main: Frontend Foundation CI → failure
    - https://github.com/Tomvaz11/iabank/actions/runs/19217803914
  - "Vault Rotation Checks" (agendado) → success
    - https://github.com/Tomvaz11/iabank/actions/runs/19219981860
- Não há evidências explícitas de testes E2E de confirmação executados para esta issue.

Observações
- A alteração de alinhamento do Poetry e remoção do `poetry lock --no-update` está refletida no branch `main`.
- Ainda assim, os últimos runs do workflow principal falharam; é recomendável reexecutar e inspecionar os logs para confirmar estabilidade após as mudanças.

---

## Validação prática recomendada

Objetivo: comprovar que (1) CI e Docker estão alinhados na versão do Poetry (1.8.3), (2) nenhum step reescreve o `poetry.lock`, e (3) o pipeline e os testes seguem verdes.

1) Ambiente local
- Instalar Poetry 1.8.3: `python -m pip install -U pip && pip install "poetry==1.8.3"`
- Instalar deps sem recriar lock: `poetry install --sync --no-interaction --no-ansi`
- Rodar testes: `pytest -q`
- Garantir que o lock não foi alterado: `git diff --exit-code poetry.lock`

2) Docker (alinhamento no container)
- Build: `docker build -t iabank-backend:test -f backend/Dockerfile .`
- Conferir versão: `docker run --rm iabank-backend:test poetry --version` (deve exibir 1.8.3)
- Sanidade de testes: `docker run --rm iabank-backend:test pytest -q`

3) CI (confirmação ponta a ponta)
- Disparar manualmente o workflow principal: `gh workflow run ".github/workflows/frontend-foundation.yml" -r main`
- Acompanhar execução: `gh run list --limit 5 --workflow ".github/workflows/frontend-foundation.yml"` e `gh run view <run_id> -v`
- Validar nos logs que:
  - `poetry --version` reporta 1.8.3;
  - Não há step com `poetry lock --no-update`;
  - `poetry install` é chamado com `--sync --no-interaction --no-ansi`;
  - Jobs de lint/test/security completam com sucesso.

4) Guardrails (opcional, mas recomendado)
- Adicionar step de verificação de versão: `poetry --version | grep 1.8.3`.
- Falhar o job se o lock for modificado: `git diff --exit-code poetry.lock` após a instalação.

