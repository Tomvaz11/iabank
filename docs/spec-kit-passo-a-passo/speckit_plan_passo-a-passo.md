# Passo a Passo — `/speckit.plan`

## Pré-requisitos
- Branch da feature criada (`git switch 002-f-10-fundacao` ou similar).
- Artefatos `spec.md` e `documentacao_oficial_spec-kit/memory/constitution.md` revisados.
- Ambiente com scripts do spec-kit disponíveis (`documentacao_oficial_spec-kit/templates/commands/plan.md`).

## Execução
1. No diretório raiz do monorepo, execute o comando indicado pelo spec-kit (ex.: `/speckit.plan --feature 002-f-10-fundacao`).
2. O agente deve rodar `scripts/bash/setup-plan.sh --json` (ou equivalente PowerShell) para obter `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR` e `BRANCH`.
3. Carregue `specs/002-f-10-fundacao/spec.md`, `specs/002-f-10-fundacao/plan.md` (template) e `documentacao_oficial_spec-kit/memory/constitution.md`.
4. Preencha o plano seguindo as seções do template: contexto técnico, checagem constitucional, fases e artefatos previstos.
5. Marque todas as pendências como `NEEDS CLARIFICATION` e converta em tarefas de pesquisa na Fase 0.
6. Gere `research.md`, `data-model.md`, os contratos preliminares e `quickstart.md` conforme as fases definidas.
7. Reavalie o checklist constitucional após preencher as fases 0 e 1.

## Saídas Esperadas
- `specs/<feature>/plan.md` preenchido sem campos `TODO`.
- `specs/<feature>/research.md`, `data-model.md`, `contracts/` e `quickstart.md` atualizados.
- Contexto do agente sincronizado via scripts `scripts/bash/update-agent-context.sh`.

## Checklist Rápido
- [ ] Script `{SCRIPT}` executado e JSON interpretado.
- [ ] Constituição citada em todas as decisões mandatórias.
- [ ] Todas as pendências resolvidas ou documentadas como riscos.
- [ ] Artefatos auxiliares gerados e versionados.
