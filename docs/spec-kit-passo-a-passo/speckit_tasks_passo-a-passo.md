# Passo a Passo — `/speckit.tasks`

## Pré-requisitos
- `specs/<feature>/plan.md` completo, sem campos `NEEDS CLARIFICATION`.
- Artefatos opcionais (`data-model.md`, `contracts/`, `research.md`, `quickstart.md`) gerados na fase anterior.
- Checklists de discovery atualizados em `specs/<feature>/checklists/`.

## Execução
1. Partindo da raiz do repositório, invoque `/speckit.tasks --feature 002-f-10-fundacao` (ajuste parâmetros conforme necessário).
2. O agente executa `scripts/bash/check-prerequisites.sh --json` para capturar `FEATURE_DIR` e `AVAILABLE_DOCS`.
3. Carregue `spec.md`, `plan.md` e demais documentos disponíveis para extrair histórias, prioridades e decisões técnicas.
4. Estruture `tasks.md` seguindo `documentacao_oficial_spec-kit/templates/commands/tasks.md`:
   - Fase 1 (Setup) → inicialização do projeto e infraestrutura comum.
   - Fase 2 (Fundacional) → blocos compartilhados entre histórias.
   - Fases seguintes → uma por user story, respeitando prioridades.
   - Fase final → polimento e cruzamentos.
5. Cada tarefa deve seguir o formato `- [ ] T00X [P] [USY] descrição (caminho/arquivo)`.
6. Gere a seção de dependências, oportunidades de paralelismo e critérios de testes independentes.
7. Valide que nenhum arquivo é referenciado por tarefas paralelas conflitantes.

## Saídas Esperadas
- `specs/<feature>/tasks.md` estruturado por fases, histórias e checklist.
- Resumo com contagem de tarefas, paralelismo e escopo MVP incluído ao final do arquivo.

## Checklist Rápido
- [ ] Script de pré-requisitos executado com sucesso.
- [ ] Todas as histórias do `spec.md` cobertas por fases dedicadas.
- [ ] IDs sequenciais `T00X` e labels `[USY]` aplicados corretamente.
- [ ] Dependências e paralelismo revisados antes de prosseguir para implementação.
