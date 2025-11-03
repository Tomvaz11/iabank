# Passo a passo pós F‑10 (Spec‑Kit)

Data: 2025-11-03

Objetivo: Consolidar o fechamento da feature F‑10 e preparar a próxima feature seguindo a metodologia do Spec‑Kit.

Observação: executar tudo a partir da raiz do repositório. Comandos `/speckit.*` são invocados no agente (ex.: Codex/Claude/Cursor) inicializado via Spec‑Kit.

## 1) Análise de consistência (obrigatória)

- Comando (no agente): `/speckit.analyze`
- Entrada considerada: `specs/002-f-10-fundacao/spec.md`, `plan.md`, `tasks.md`, e `memory/constitution.md`.
- O que fazer com o relatório:
  - Resolver itens CRITICAL e HIGH antes de encerrar a feature.
  - Ajustar `spec.md`, `plan.md` ou `tasks.md` conforme as recomendações.
  - Reexecutar `/speckit.analyze` até não haver bloqueios.

Referência: `documentacao_oficial_spec-kit/templates/commands/analyze.md`.

## 2) Checklists de requisitos (recomendado)

- Comando (no agente): `/speckit.checklist <tema>`
- Onde salvar: `specs/002-f-10-fundacao/checklists/<tema>.md`.
- Temas sugeridos: `geral`, `api`, `ux`, `seguranca`, `performance`.
- Critério de saída: todos os itens marcados (`[x]`). Se houver pendências, decidir explicitamente se podem ficar para depois antes do merge.

Referência: `documentacao_oficial_spec-kit/templates/commands/checklist.md` e `.../templates/checklist-template.md`.

## 3) Confirmar tasks da F‑10

- Verificar `specs/002-f-10-fundacao/tasks.md` está com 100% das tarefas marcadas como concluídas.
- Garantir que “Checkpoints” por história e fase final estejam consistentes com as evidências.

## 4) Validações locais e gates (Quickstart)

Executar do repositório raiz (ajuste variáveis conforme necessário):

```bash
pnpm install
pnpm lint
pnpm test
pnpm storybook # opcional para inspeção local
pnpm chromatic --project-token $CHROMATIC_PROJECT_TOKEN --exit-zero-on-changes
pnpm pact:verify
pnpm lighthouse --config frontend/lighthouse.config.mjs
pnpm k6 run tests/performance/frontend-smoke.js
# Backend (Python)
poetry install --with dev
poetry run ruff check .
poetry run pytest -q --maxfail=1 --disable-warnings
# (Opcional) cobertura consolidada
poetry run coverage run -m pytest && poetry run coverage report -m
```

Gates mínimos (conforme plano/artefatos da F‑10):
- Cobertura de testes (frontend + backend) ≥ 85%.
- Lighthouse budgets: LCP ≤ 2.5s (p95) e TTI ≤ 3.0s.
- SAST (Semgrep): sem High/Critical pendentes em release.
- DAST (OWASP ZAP baseline): sem falhas críticas.
- SCA (pnpm audit / safety/pip-audit) + SBOM CycloneDX: sem High/Critical.
- Pact/Spectral/OpenAPI-diff: contratos estáveis e coerentes.
- Chromatic: cobertura visual ≥ 95% por tenant; sem violações axe-core.
- RLS/Segurança de dados: testes de enforcement RLS e pgcrypto aprovados.
- CSP & Trusted Types: sem violações (fase report-only) e, após migração, sem violações em modo enforce.

Atualizar evidências/documentação:
- Runbook: `docs/runbooks/frontend-foundation.md` (resultados, flags, procedimentos, gates).
- Dashboards: `observabilidade/dashboards/frontend-foundation.json` (métricas SC‑001..SC‑005).
- Threat model: `docs/security/threat-models/frontend-foundation/<release>.md` (usar template em `docs/security/threat-model-template.md`).
- FinOps: executar `pnpm finops:report` e anexar saída ao dashboard/runbook.
- Telemetria: executar `pnpm foundation:otel verify --tenant <tenant>` e anexar evidências de mascaramento de PII e correlação trace.
- Contratos: `pnpm openapi:pull && pnpm openapi:diff && pnpm openapi:generate && pnpm pact:publish` quando aplicável.

## 5) Consolidação de branches e PR

Mesclar a validação na branch da feature:

```bash
git checkout 002-f-10-fundacao
git merge --no-ff validation-v2-final
# resolver conflitos se houver
git push -u origin 002-f-10-fundacao
```

Abrir PR de `002-f-10-fundacao` para `main`:

- Título: “F‑10 Fundação Frontend FSD e UI Compartilhada”.
- Labels sugeridos: `foundation`, `frontend`.
- Descrição (linkar artefatos):
  - `specs/002-f-10-fundacao/spec.md`
  - `specs/002-f-10-fundacao/plan.md`
  - `specs/002-f-10-fundacao/tasks.md`
  - `specs/002-f-10-fundacao/quickstart.md`
  - Evidências: runbook, dashboards, checklists, threat model.

Opcional (via GitHub CLI):

```bash
gh pr create -B main -H 002-f-10-fundacao \
  -t "F-10 Fundação Frontend FSD e UI Compartilhada" \
  -b "Resumo, artefatos e evidências:\n\n- specs/002-f-10-fundacao/spec.md\n- specs/002-f-10-fundacao/plan.md\n- specs/002-f-10-fundacao/tasks.md\n- specs/002-f-10-fundacao/quickstart.md\n- docs/runbooks/frontend-foundation.md\n- observabilidade/dashboards/frontend-foundation.json\n- docs/security/threat-models/frontend-foundation/<release>.md"
```

Referência: `documentacao_oficial_spec-kit/README.md` (STEP 5/7) e `docs/quickstart.md`.

## 6) Pós‑merge

- Verificar pipelines na `main` e sincronização GitOps (Argo CD) para manifests em `infra/argocd/frontend-foundation`.
- Checar dashboards/alertas e fechar tarefas relacionadas nos runbooks/checklists.
- Apagar branch de validação criada por engano após merge efetivo das mudanças:

```bash
git branch -D validation-v2-final || true
git push origin :validation-v2-final || true
```

UAT & Exploratório:
- Conduzir uma passagem de testes exploratórios e uma sessão de UAT com stakeholders.
- Registrar feedback e, se necessário, abrir issues/mini-features seguindo o fluxo do Spec‑Kit.

Observabilidade pós‑deploy (24–48h):
- Monitorar SC‑001..SC‑005, erros, performance e segurança.
- Confirmar ausência de regressões e violações (CSP/Trusted Types/PII) em produção.

## 7) Próxima feature (seguir o índice)

Criar nova feature e iniciar o ciclo Spec‑Kit:

```bash
.specify/scripts/bash/create-new-feature.sh "<Descrição da próxima feature>" --short-name "proxima-feature"
```

No agente, seguir a ordem:
- `/speckit.specify` (especificação, focar no “o quê/por quê”).
- `/speckit.clarify` (opcional, recomendado).
- `/speckit.plan` (gera plan.md, research.md, data-model.md, contracts/, quickstart.md).
- `/speckit.tasks` (gera tasks.md ordenado por dependências e por história).
- `/speckit.analyze` (consistência entre spec/plan/tasks, read-only).
- `/speckit.checklist` (opcional, requisitos bem escritos por tema).
- `/speckit.implement` (execução conforme tasks.md, respeitando TDD e gates).

Referências dos comandos: `documentacao_oficial_spec-kit/templates/commands/*.md`.

## 8) Critérios de aceite para encerrar a F‑10

- `/speckit.analyze` sem CRITICAL/HIGH pendentes.
- Checklists pertinentes 100% marcadas ou pendências explicitamente aceitas.
- `tasks.md` 100% concluído e consistente com a implementação.
- Gates de qualidade/performance/segurança atendidos (cobertura ≥ 85%, LCP/TTI dentro de budget, SAST/DAST/SCA/SBOM sem High/Critical, contratos OK).
- Runbook/dashboards/threat model atualizados e vinculados ao PR.
- PR aprovado e mergeado na `main`; monitoramento pós‑deploy sem regressões.
- Constituição: "Constitution Check" do `plan.md` aprovado (sem violações) e seção "Complexity Tracking" vazia ou com exceções justificadas e aceitas.
- Sucesso do produto: todos os Success Criteria definidos em `spec.md` estão mapeados a evidências (testes, métricas, screenshots, relatórios) e marcados como atingidos.

---

Anexos úteis:

- F‑10 Plan: `specs/002-f-10-fundacao/plan.md`
- F‑10 Tasks: `specs/002-f-10-fundacao/tasks.md`
- F‑10 Quickstart: `specs/002-f-10-fundacao/quickstart.md`
- Documentação Spec‑Kit: `documentacao_oficial_spec-kit/README.md`, `docs/quickstart.md`, `templates/commands/*`
