# Runbook — Fundação Frontend FSD e UI Compartilhada

Escopo
- Ativação/rollback das flags `foundation.fsd` e `design-system.theming` por tenant.
- Procedimentos para incidentes de Chromatic/Lighthouse/a11y.
- Operação de CSP/Trusted Types (report-only → enforce) e evidências LGPD/RLS.
- Gestão de FinOps, throughput/saturação (NFR-005/NFR-007) e política de outage no CI (NFR-008).

Pré-requisitos
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
