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

- Acesso a ConfigCat (ou feature flag provider) nos ambientes.
- Acesso a observabilidade e Sentry.
- Permissões de deploy via Argo CD.

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
- Executar diariamente `pnpm ts-node scripts/finops/foundation-costs.ts` (ou job CI programado) para coletar custos de Chromatic, Lighthouse e pipelines, com tagging `tenant`/`feature`.
- Alertas automáticos em 80% e 100% do orçamento mensal notificam Frontend Foundation Guild e FinOps chapter; registrar ações corretivas no runbook.
- Avaliar trims de snapshots, paralelização e caching quando o consumo exceder 80%; documentar decisões em "Notas FinOps".

CSP e Trusted Types
- Report‑Only por 30 dias: cabeçalho `Content-Security-Policy-Report-Only` com `script-src 'strict-dynamic' 'nonce-{RANDOM}'`; `require-trusted-types-for 'script'; trusted-types foundation-ui`.
- Enforcement: mover diretivas para `Content-Security-Policy` e garantir injeção de nonce pelo gateway (NJS) em todas as tags `<script>` do index.html.
- Dev local: plugin Vite injeta nonce e mantém TT em report-only.
- Auditar violações e abrir follow-ups.

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
