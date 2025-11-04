# Passo a Passo — `/speckit.implement`

## Pré-requisitos
- `specs/<feature>/tasks.md` aprovado, sem lacunas no checklist.
- Checklists em `specs/<feature>/checklists/` atualizados; itens críticos devem estar marcados como completo ou mapeados para tarefas iniciais.
- Ambiente local com dependências instaladas (`pnpm install`, ferramentas pact, Spectral, etc.).

## Execução
1. A partir da raiz do repo, execute `/speckit.implement --feature 002-f-10-fundacao`.
2. O agente roda `scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` para validar artefatos e ler `tasks.md`.
3. Avalie o status das checklists: se houver itens pendentes, confirme manualmente com o solicitante antes de continuar.
4. Carregue `plan.md`, `tasks.md`, `data-model.md`, `contracts/`, `research.md` e `quickstart.md` para entender dependências, SLAs e requisitos técnicos.
5. Antes de codificar, garanta que arquivos de ignore (.gitignore, .dockerignore, etc.) estejam atualizados conforme as tecnologias detectadas.
6. Execute as fases em ordem, respeitando dependências e marcadores `[P]`:
   - Tarefas de testes precedem as de implementação.
   - Trabalhos sobre o mesmo arquivo não devem ocorrer em paralelo.
7. Após concluir cada tarefa, marque o item correspondente em `tasks.md` com `[X]` e registre evidências (commits, resultados de testes, links de dashboard).
8. Ao final de cada fase, valide cobertura de testes pact/contract, lint e qualquer gate listado em `plan.md`.

## Saídas Esperadas
- Tarefas concluídas e marcadas em `specs/<feature>/tasks.md`.
- Artefatos atualizados (código, contratos, documentação, runbooks).
- Logs de execução ou relatórios anexados à PR conforme exigências do processo.

## Checklist Rápido
- [ ] Pré-requisitos confirmados pelo script do spec-kit.
- [ ] Itens de checklist resolvidos ou assumidos conscientemente.
- [ ] Tarefas marcadas com `[X]` ao finalizar cada entrega.
- [ ] Geração de evidências (testes, screenshots, links) antes do merge.
