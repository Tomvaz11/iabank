# Issue #86 — Resumo de Estado e Validação Prática

## Estado Atual
- Título: CI: Melhorias rápidas F-10 (poetry flags, cache/checks, DRY, summaries, renovate pin, outage retries, pre-commit)
- URL: https://github.com/Tomvaz11/iabank/issues/86
- Situação: CLOSED
- Autor: @Tomvaz11
- Criada em: 2025-11-09 15:31:13Z
- Fechada em: 2025-11-10 01:30:56Z
- Assignees/Labels/Milestone: sem assignees, sem labels, sem milestone

### Corpo/Checklist da Issue
Pacote de melhorias rápidas (baixo esforço, alto valor):
- Python/Poetry no CI: usar `poetry install --no-interaction --no-ansi --sync`.
- Cache Node/pnpm: revisar invalidação se `scripts/**` impactar build.
- Serviços DB no CI: conectar via hostname do serviço (`postgres:5432`) e evitar mapear porta do host.
- DRY nos workflows: extrair blocos repetidos (checkout/setup/install) para reusable workflows/ação composta.
- Step summaries: publicar resumos de lint/test/perf (Lighthouse) no `GITHUB_STEP_SUMMARY`.
- Renovate validator: trocar `renovate@latest` por faixa major estável no validador.
- Outage policy: adicionar retry/backoff em `scripts/ci/handle-outage.ts`.
- Pre-commit no CI (opcional): rodar `pre-commit run --all-files` em job leve.

Observação: na própria issue nenhum item do checklist foi marcado, porém há evidências em comentários e pipelines.

### Comentários Relevantes
- 2025-11-09 22:40:25Z: “Subtarefa concluída: Renovate com pin global (...). Implementado em main no commit fd73c214. PR #88 fechado como redundante.”
- 2025-11-10 01:30:55Z: “Configurado em renovate.json (rangeStrategy=pin e :pinDigests presentes).”

### PRs Relacionados
- PR #88 — chore(renovate): pin de versões global (#86)
  - Estado: CLOSED (não mergeado; mudanças aplicadas direto na main)
  - Base: `main`; Head: `issue-86-renovate-pin`

### Execuções de CI Relacionadas à #86
- Run 19213960593 — “Renovate Config Validation” — concluído com sucesso.
- Run 19213960584 — “Frontend Foundation CI” — falhou no job “Lint” (checagem de template de PR); jobs de testes (Vitest), contratos, segurança, performance/E2E ficaram “skipped”.

### E2E/Confirmação de ponta a ponta
- Não há registro de E2E concluído e aprovado específico para o escopo da #86. No run vinculado à #86, os jobs que executariam E2E e gates ficaram “skipped”. Há E2E recentes em branches de #85/#81, porém com falhas e sem relação direta com #86.

## Conclusão
- Implementação: Parcial e focada no “Renovate pin” (aplicado na `main` e validado). Os demais itens do checklist não possuem comprovação inequívoca via PR/CI atrelado à #86, e não houve execução E2E aprovada para esta issue.

## Validação Prática Recomendada
Objetivo: Exercitar, em um PR canário, todos os pontos do checklist da #86 com evidência em logs e summaries do GitHub Actions.

1) Renovate pin (confirmação)
- Acionar o workflow “Renovate Config Validation” a partir de uma branch canário; verificar sucesso.
- Opcional: simular uma atualização para confirmar que Renovate gera PRs com versões pinadas e digests.

2) Poetry no CI (backend)
- Garantir que o job backend use exatamente: `poetry install --no-interaction --no-ansi --sync`.
- Confirmar que `pytest` roda limpo e que o job não altera `poetry.lock` (logs sem diffs).

3) Cache pnpm sensível a `scripts/**`
- Abrir PR alterando arquivo em `scripts/**` e observar nos logs de cache: “cache miss” antes do `pnpm install`.
- Comparar tempos de instalação entre execuções (warm vs cold) para aferir invalidação.

4) Serviços DB por hostname
- Em job com Postgres como serviço, validar: `pg_isready -h postgres -p 5432`.
- Rodar testes de integração que usem `postgres:5432` (sem mapear porta do host) e verificar conexão ok.

5) DRY + Step Summaries
- Confirmar que os workflows usam blocos reutilizáveis/ação composta para checkout/setup/install.
- Conferir o “Summary” (GITHUB_STEP_SUMMARY) com seções de lint/test/perf.

6) Outage policy (retry/backoff)
- Executar o “Outage Guard” apontando para endpoint indisponível; observar tentativas com backoff e término controlado (sem falha ruidosa do pipeline; logs evidenciam retries).

7) Pre-commit (opcional)
- Habilitar job leve executando `pre-commit run --all-files` e conferir sucesso + resumo no “Summary”.

Critérios de aceite
- Um PR canário executa o pipeline completo (se aplicável, com `CI_ENFORCE_FULL_SECURITY=true`), exibindo:
  - Renovate validator ok; Poetry com flags corretas; cache pnpm invalidando ao tocar `scripts/**`;
  - Testes passando (incl. integração com DB via hostname);
  - Summaries de lint/test/perf (Lighthouse) visíveis; ZAP/Lighthouse se aplicável;
  - Outage Guard com retries/backoff evidenciados;
  - Pre-commit (se habilitado) verde.

