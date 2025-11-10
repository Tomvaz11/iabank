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

---

## Validação executada (agora)

Data/hora (UTC): 2025-11-10T19:40:00Z

Ações realizadas
- GitHub Actions:
  - Tentativa de `workflow_dispatch` do workflow principal: HTTP 422 — “Workflow does not have 'workflow_dispatch' trigger”.
  - Reexecução de run anterior: não permitido (“workflow file may be broken”).
  - Corrigido erro de YAML (passo “Resumo ZAP”) no workflow.
  - Disparo por push em `chore/issue-83-validation-ci` após a correção:
    - Run: 19243783235 — conclusão: success
      - Link: https://github.com/Tomvaz11/iabank/actions/runs/19243783235

- Docker (ambiente controlado):
  - Build da imagem `iabank-backend:test` OK.
  - Log de instalação mostra “Installing Poetry (1.8.3)” e finaliza OK.
  - Comandos validados no container:
    - `poetry --version` → “Poetry (version 1.8.3)”.
    - `poetry install --with dev --no-ansi --no-interaction --no-root` foi executado na build com sucesso (sem `poetry lock`).
  - `pytest` dentro do container retornou erro de configuração do Django (settings/DB), não conclusivo para a saúde dos testes, mas não afeta a validação do alinhamento do Poetry.

Conclusão da validação
- Alinhamento do Poetry para 1.8.3 e remoção do `poetry lock --no-update` confirmados no Dockerfile e no workflow do CI.
- Execução ponta a ponta via GitHub Actions foi realizada com sucesso no branch de validação após correção do YAML. Poetry 1.8.3 instalado e `poetry install --with dev --no-ansi --no-interaction` utilizado; nenhum `poetry lock` executado.

Próximos passos sugeridos
- Abrir/acompanhar PR para levar a correção de YAML ao `main`: https://github.com/Tomvaz11/iabank/pull/119
- Após merge, revalidar um push em `main` para assegurar estabilidade contínua do pipeline.

---

## Atualizações adicionais

- Guardrails no CI: adicionados passos para verificar a versão do Poetry (1.8.3) e garantir que o `poetry.lock` não foi alterado (via `git diff --exit-code poetry.lock`).
- Documentação alinhada ao padrão:
  - `README.md`: pré‑requisito Poetry 1.8.3 e uso de `poetry install --with dev --sync --no-interaction --no-ansi`.
  - `CONTRIBUTING.md`: seção de Ambiente Python/Poetry com comandos recomendados.
  - `docs/lgpd/rls-evidence.md`: preparação de ambiente com Poetry 1.8.3.
  - `docs/runbooks/frontend-foundation.md`: nota sobre validação com Poetry 1.8.3.
- PR aberto com esses ajustes: https://github.com/Tomvaz11/iabank/pull/120

\n<!-- CI validation trigger: 2025-11-10T19:23:13Z -->
