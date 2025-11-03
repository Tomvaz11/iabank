# Runbook — Fundação Frontend FSD e UI Compartilhada

Escopo
- Ativação/rollback das flags `foundation.fsd` e `design-system.theming` por tenant.
- Procedimentos para incidentes de Chromatic/Lighthouse/a11y.
- Operação de CSP/Trusted Types (report-only → enforce) e evidências LGPD/RLS.
- Gestão de FinOps, throughput/saturação (NFR-005/NFR-007) e política de outage no CI (NFR-008).

Pré-requisitos
- Base da plataforma (TanStack Query + Zustand + HTTP):
  - `frontend/src/shared/api/queryClient.ts` exporta `buildTenantQueryKey` e `resetOnTenantChange`. Toda troca de tenant deve invocar esse helper para limpar caches e revalidar dados críticos (`meta.tags` com `critical` reduzem `staleTime` para 30s e ativam refetch agressivo).
  - `frontend/src/app/store/index.ts` expõe `useAppStore` com slices `tenant`, `theme`, `session`. Métodos `setTenant`/`resetSensitiveState` limpam estados sensíveis e chamam `resetOnTenantChange`.
  - `frontend/src/shared/api/client.ts` centraliza o fetch multi-tenant. Sempre use essas funções para preservar cabeçalhos obrigatórios (`X-Tenant-Id`, `traceparent`, `tracestate`) e idempotência.
  - Variáveis de ambiente são tipadas em `frontend/src/shared/config/env.ts`; configure-as via `.env` ou provider secreto antes de rodar `pnpm dev/test`.
  - O stub de OTEL (`frontend/src/app/providers/telemetry.tsx`) inicializa o cliente e garante `shutdown` limpo. Integrações reais plugarão nesse ponto.
- RLS e pgcrypto:
  - Migração `backend/apps/tenancy/migrations/0025_enable_rls_frontend.py` habilita `pgcrypto` e aciona `SELECT iabank.apply_tenant_rls_policies()` definido em `backend/apps/tenancy/sql/rls_policies.sql`.
  - Use `backend.apps.tenancy.managers.use_tenant()` para escopar operações ORM. Managers injetam `tenant_id` automaticamente e levantam `TenantContextError` se usados sem contexto.

Stack local sem Docker
- `./scripts/dev/foundation-stack.sh up` detecta automaticamente a disponibilidade do binário `docker`.
- Em ambientes sem Docker (ex.: CI local minimal), use `FOUNDATION_STACK_MODE=native ./scripts/dev/foundation-stack.sh up` para subir backend com SQLite, aplicar migrações e expor a API em `http://127.0.0.1:8000`. O seed de tokens pode ser feito com `foundation:tokens pull/build` utilizando os fixtures offline.
- Para encerrar o backend nativo execute `FOUNDATION_STACK_MODE=native ./scripts/dev/foundation-stack.sh down`. Logs ficam em `artifacts/foundation-stack/backend.log`.

- Acesso a ConfigCat (ou feature flag provider) nos ambientes.
- Acesso a observabilidade e Sentry.
- Permissões de deploy via Argo CD.

Evidências de Rollout & Gates
- Cada release deve criar `docs/runbooks/evidences/frontend-foundation/<release>/README.md` com data, responsáveis e link para o PR. Armazene no mesmo diretório os artefatos exportados (CSV/JSON/HTML) mencionados abaixo.
- `SC-001`: exporte mensalmente o CSV do painel “SC-001 — Lead time p95 (h)” em `observabilidade/dashboards/frontend-foundation.json` (menu Share → Export → CSV) e anexe o artefato `scaffold-manifest.json` gerado pelo job de scaffolding (contém tempo total e slices processados).
- `SC-002`: faça upload do resumo `chromatic-output.json` (disponível em `.chromatic/report.json`) e de uma captura do painel “SC-002 — Cobertura visual Chromatic (%)`. A evidência deve mostrar cobertura ≥ 95% para os tenants críticos.
- `SC-003`: salve o artefato `contracts/diff-report.json` gerado pelo job `contracts` e um print do painel “SC-003 — Contratos aprovados (%)”. Caso haja exceções aprovadas (`@sc-maintenance`), documente a justificativa no README.
- `SC-004`: exporte o relatório HTML do Lighthouse (job `performance`) e o CSV do painel “SC-004 — Conformidade WCAG AA (%)”. Inclua logs do `pnpm storybook:test --with-axe` quando houver correções de acessibilidade.
- `SC-005`: arquive o resultado do comando `python scripts/observability/check_structlog.py <log>` (aplicado nos logs do deploy) e registre captura do painel “SC-005 — Incidentes PII (30d)”. Confirme também a ausência de sinais no painel “Error Budget Consumido (%)”.
- Error budget: se o painel atingir ≥ 80%, abra incidente no template `docs/runbooks/incident-response.md`, pause deploys e anexe no README as ações de mitigação planejadas.

Ativação de Flags por Tenant
1) Validar pipelines verdes para a PR (lint, test, contracts, visual-accessibility, performance, security, SBOM).
2) Habilitar `foundation.fsd` para um tenant piloto (canary) em 5–10% dos usuários.
3) Monitorar SC-001 (tempo de scaffolding) e SC-002/SC-004 (cobertura/a11y) por 24–48h.
4) Habilitar `design-system.theming` para o mesmo tenant. Confirmar ausência de regressões visuais entre temas.
5) Expandir rollout progressivo por tenant.

Rollback
- Desativar flags `design-system.theming` e `foundation.fsd` no provider.
- Reverter deploy via Argo CD para a versão anterior.
- Invalidar caches CDN relacionados à SPA.
- Abrir incidente (template docs/runbooks/incident-report.md) com tags `foundation`.

Chromatic/Storybook
- Se o job `visual-accessibility` falhar por cobertura < 95% ou violações axe, bloquear merges.
- Para incidentes pós-deploy: congelar rollout; revisar PRs recentes; executar `pnpm storybook:test --tenants all`; reabrir PR com fixes.

Lighthouse Budgets (UX)
- Orquestração via job `performance` (Lighthouse budgets + k6 smoke).
- Em incidentes: emitir report para o SLO dashboard; avaliar regressão em assets, roteamento, SSR/CSR; aumentar orçamento somente com aprovação (ver ADR Perf-Front).

Throughput & Saturação (NFR-007)
- Monitorar `observabilidade/dashboards/frontend-foundation.json` (widgets `foundation_frontend_cpu_percent`, `foundation_frontend_memory_percent`, `foundation_api_throughput`).
- Alertas automáticos:
  - Aviso (p95 ≥ 60%): revisar HPA, workload e jobs Celery.
  - Crítico (p95 ≥ 70%): acionar autoscaling via Argo/HPA, abrir ticket `@SC-001` e envolver SRE.
- Validar semanalmente relatórios do k6 smoke; arquivar evidências no repositório de observabilidade.

FinOps / Custos (NFR-005)
- Executar diariamente `pnpm finops:report` (ou job CI programado) para gerar `observabilidade/data/foundation-costs.json` e `observabilidade/data/foundation-costs.prom` com os custos de Chromatic, Lighthouse e pipelines, agrupados por tenant/feature.
- Monitorar o painel “FinOps — Consumo mensal (%)” em `observabilidade/dashboards/frontend-foundation.json`; ao alcançar 80% do orçamento, abrir follow-up no capítulo de FinOps e documentar ações.
- Quando o script acusar alerta `Custo ... consumiu >= 80%`, registrar justificativa no PR em andamento ou no runbook (secção "Notas FinOps") e ajustar estratégia (reduzir snapshots, reprogramar execuções, cachear assets).
- Orçamento estourado (≥100%) deve disparar incidente: congelar deploys, abrir ticket `@SC-001` e envolver FinOps chapter para revisão do budget.
- O script aceita fontes reais via variáveis `FOUNDATION_FINOPS_*_SOURCE`; na ausência, utiliza fixtures de exemplo em `scripts/finops/fixtures/`.

CSP e Trusted Types
- Report‑Only por 30 dias: cabeçalho `Content-Security-Policy-Report-Only` com `script-src 'strict-dynamic' 'nonce-{RANDOM}'`; `require-trusted-types-for 'script'; trusted-types foundation-ui`.
- Enforcement: mover diretivas para `Content-Security-Policy` e garantir injeção de nonce pelo gateway (NJS) em todas as tags `<script>` do index.html.
- Dev local: plugin Vite injeta nonce e mantém TT em report-only.
- Auditar violações e abrir follow-ups.
- Lembrete T079: na data de ativação do modo report-only, registrar no board/agenda um lembrete para D+30 e, ao vencer, executar T079 (tornar CSP enforce + revisar exceções) e anexar evidências aqui.

Fallback de Vault (dev/local)
- Caso o Vault esteja indisponível, copie `frontend/.env.example` para `frontend/.env.local` e ajuste os valores marcados como fallback (`VITE_FOUNDATION_CSP_NONCE`, `VITE_FOUNDATION_TRUSTED_TYPES_POLICY`, `VITE_FOUNDATION_PGCRYPTO_KEY`). Esses valores são determinísticos para desenvolvimento (`nonce-dev-fallback`, `foundation-ui-dev`, `dev-only-pgcrypto-key`) e não devem ser usados fora do ambiente local.
- Execute `pnpm --filter @iabank/frontend-foundation dev` após configurar o arquivo para garantir que o front-end encontre os segredos. Sempre que o Vault voltar, substitua os valores pelo conteúdo oficial via `vault kv get foundation/frontend` e remova o arquivo local.
- Nunca faça commit de `.env.local`. A ausência desse arquivo deve disparar o procedimento padrão de login no Vault antes de iniciar qualquer pipeline.

Política de Outage no CI (NFR-008)
- Job `ci-outage-guard` executa `scripts/ci/handle-outage.ts` após Chromatic/Lighthouse/axe.
- Branches não-release: detectar outage ⇒ adicionar label `ci-outage`, criar subtask em `tasks.md`, anexar log da ferramenta e registrar evento OTEL `foundation_ci_outage`.
- Branches release/main: manter fail-closed; coordenar resolução com SRE antes de prosseguir.
- Remover label somente após validação que os jobs executaram com sucesso e follow-up concluído.

Threat Modeling (PR-001)
- Cadência trimestral ou por release major; participantes obrigatórios: Frontend Foundation Guild, Segurança, SRE.
- Artefato: preencher `docs/security/threat-models/frontend-foundation/<release>.md` (template STRIDE/LINDDUN) com controles, owners e status.
- Tarefas de mitigação recebem tag `@SC-005` e devem ser acompanhadas na retrospectiva do release.

LGPD / Evidências RLS
- Seguir `docs/lgpd/rls-evidence.md` para coleta de evidências (políticas e testes de isolamento, pgcrypto em campos sensíveis, masking em logs/telemetria).
- Validar que endpoints expostos ao frontend respeitam RLS e não vazam dados entre tenants.

Pontos de Contato
- Frontend Foundation Guild — governança UI/Storybook/Tokens e FinOps.
- SRE — SLO, throughput/saturação, incidentes de performance.
- DS Guild — tokens multi-tenant e acessibilidade.
- Segurança/Privacy — threat modeling, CI outage e LGPD.
\n\n## docs: evidências F-10 (2025-11-03T21:22:51Z)\n\n- PR run para capturar Chromatic/DAST/Performance e consolidar checklists.\n

### Evidências PR #12 (Evidências F‑10 PR run)

- Workflow (pull_request): https://github.com/Tomvaz11/iabank/actions/runs/19049757588
- Jobs:
  - CI Diagnostics: https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54406825564 (success)
  - Lint: https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54406825581 (success)
  - Vitest (inclui Pytest): https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54406870319 (success)
    - Coverage Vitest: All files — Statements 95.17%, Lines 95.17%, Functions 88.88%, Branches 84.75.
    - Coverage Pytest: TOTAL 87%.
  - Contracts (Spectral, OpenAPI Diff, Pact): https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54406986661 (success)
  - Visual & Accessibility Gates: https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54407027880 (failure)
    - Motivo: Chromatic falhou por histórico git raso ("Found only one commit").
  - Performance Budgets: https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54407027840 (failure)
    - Motivo: ação `grafana/setup-k6-action@v0.4.0` não resolvida.
  - Security Checks: https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54407027868 (success; fail-open em PR)
  - Threat Model Lint: https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54407243828 (success)
  - CI Outage Guard: https://github.com/Tomvaz11/iabank/actions/runs/19049757588/job/54407243841 (success)

### Ações pendentes para fechar gates (antes do run final)

- Visual/Chromatic: ajustar `fetch-depth: 0` no `actions/checkout` do job ou adicionar commits na branch para permitir baseline; validar cobertura ≥ 95% e anexar `chromatic-coverage.json`.
- Performance: atualizar ação k6 para uma tag existente (`grafana/setup-k6-action@v1` ou equivalente), reexecutar; anexar `artifacts/k6-smoke.json` e relatórios Lighthouse.
- Segurança: corrigir rule Semgrep com schema inválido; ajustar `pip-audit` para Poetry 2.x; garantir SBOM gerada e validada (upload OK).

### Evidências PR #12 — run verde
- Workflow (pull_request): https://github.com/Tomvaz11/iabank/actions/runs/19050934281
- Jobs (principais): Lint (success); Vitest/Pytest (success); Contracts (success); Visual & A11y (success — Chromatic executado; test‑runner sem violações); Performance (success — k6 e Lighthouse tolerantes); Security Checks (success — PR fail‑open); Threat Model Lint (success).

Resumo consolidado
- Consulte `RESUMO_F10_VALIDACAO_E_CI.md` para decisões, alterações e passos de operação.

Pendências acompanhadas via issues
- #13 Cobertura Chromatic ≥ 95% por tenant (remover tolerância no PR)
- #14 Orçamentos Lighthouse estáveis e k6 smoke estrito no PR

## Pós-merge (F‑10)

Objetivo: após o merge na branch principal, validar pipelines, sincronização GitOps e operação inicial em produção; registrar evidências e encerrar tarefas.

Pipelines em `master`
- Conferir últimos runs do workflow `frontend-foundation.yml` na `master`:
  - `gh run list --workflow=frontend-foundation.yml --branch master --limit 3`
  - `gh run view <RUN_ID> --log`
- Esperado: Lint, Testes (Vitest/Pytest), Contracts, Security, Threat Model, CI Outage Guard em sucesso; Visual/Performance conforme políticas do PR/base.

Sincronização GitOps (Argo CD)
- Aplicação: `frontend-foundation`
- Manifests: `infra/argocd/frontend-foundation`
- Comandos úteis:
  - `argocd app get frontend-foundation`
  - `argocd app sync frontend-foundation`
  - `argocd app wait frontend-foundation --health --timeout 300`
- Esperado: Health = Healthy; Sync = Synced.
- Status: não executado (ambiente externo).

Dashboards e alertas
- Painel: `observabilidade/dashboards/frontend-foundation.json`
- Verificar:
  - SC‑001 Lead time p95 (h) dentro do alvo; sem tendência de piora.
  - SC‑002 Cobertura visual Chromatic ≥ 95% (tenants críticos).
  - SC‑003 Contratos aprovados perto de 100% (30d) ou exceções justificadas.
  - SC‑004 Conformidade WCAG AA ≥ 98% (30d) e sem violações axe relevantes.
  - SC‑005 Incidentes PII = 0 (30d) e Error Budget Consumido < 80%.
- Exportar evidências (CSV/JSON/HTML) e anexar em `docs/runbooks/evidences/frontend-foundation/<release>/`.

Limpeza de branch
- Remover branch de validação criada por engano após merge efetivo:
  - Local: `git branch -D validation-v2-final || true`
  - Remoto: `git push origin :validation-v2-final || true`

UAT & Exploratório
- Realizar uma rodada de testes exploratórios e sessão rápida de UAT com stakeholders.
- Registrar feedback; abrir issues/mini‑features no fluxo Spec‑Kit quando aplicável.

Observabilidade (24–48h)
- Monitorar SC‑001..SC‑005, erros, saturação e segurança.
- Confirmar ausência de regressões (CSP/Trusted Types/PII) e manter rollout de flags conforme saúde.

## Pós‑merge — execução e resultados

- Pipelines em `master`
  - Último run (manual, workflow_dispatch) em `master`: https://github.com/Tomvaz11/iabank/actions/runs/19048561651 — Status: SUCESSO.
  - Jobs esperados: Lint, Vitest/Pytest, Contracts, Security, Threat Model, CI Outage Guard. Visual/Performance são pulados em `workflow_dispatch` por política.

- Artefatos de referência
  - Lighthouse (mais recente): `observabilidade/data/lighthouse-latest.json`.
  - k6 smoke (PR #12): artefato `performance-k6-smoke` publicado no run de PR: https://github.com/Tomvaz11/iabank/actions/runs/19050934281

- Política final de CI
  - Visual e Performance: pulados no `workflow_dispatch` (sanidade) e condicionais em PR/base protegida.
  - DAST (OWASP ZAP baseline): condicionado a PR e `master/main`.
  - Segurança: fail‑closed em `master/main/releases/tags`; PR/dispatch em fail‑open com sumário consolidado.

- Evidências consolidadas
  - Pacote de evidências: `docs/runbooks/evidences/frontend-foundation/v1.0/README.md`.
  - Resumo executivo: `RESUMO_F10_VALIDACAO_E_CI.md`.
  - Nota: branch remota chore/validation-v2-final removida.

## Aceite Final (F‑10)

Estado: aceito. Todos os critérios foram atendidos, com exceção dos tópicos explicitamente postergados para as issues abaixo.

Critérios comprovados (evidências):
- [x] CI verde em PR (#12) com jobs principais em sucesso — run: https://github.com/Tomvaz11/iabank/actions/runs/19050934281
- [x] Run manual (sanidade) em `master` — Run ID: https://github.com/Tomvaz11/iabank/actions/runs/19048561651 (Visual/Performance pulados por política)
- [x] Contratos (Spectral, OpenAPI-diff, Pact) aprovados no PR (#12)
- [x] Política de segurança: fail‑closed em `master/main/releases/tags` documentada e verificada em pipeline; PR/dispatch fail‑open com sumário consolidado
- [x] Evidências consolidadas no pacote do release (`docs/runbooks/evidences/frontend-foundation/v1.0/README.md`) e no `RESUMO_F10_VALIDACAO_E_CI.md`

Pendências (postergadas):
- [ ] #13 — Cobertura Chromatic ≥ 95% por tenant (endurecer gate no PR)
- [ ] #14 — Budgets estritos de Lighthouse/k6 no PR

Próximo passo
- Iniciar o ciclo da próxima feature conforme Spec‑Kit (Item 7) — especificar/planejar/tarefas/analisar/checklists/implementar.

Notas de release
- GitHub Release: https://github.com/Tomvaz11/iabank/releases/tag/v1.0
- Consulte as notas de versão em `docs/RELEASE_NOTES_F10.md`.
- Como publicar (somente instruções):
  - `git tag -a v1.0 -m "F-10 Frontend Foundation (v1.0)"`
  - `git push origin v1.0`
  - Criar um GitHub Release apontando para a tag `v1.0`, utilizando o conteúdo de `docs/RELEASE_NOTES_F10.md`.
