# Runbook — Fundação Frontend FSD e UI Compartilhada

Escopo
- Ativação/rollback das flags `foundation.fsd` e `design-system.theming` por tenant.
- Procedimentos para incidentes de Chromatic/Lighthouse/a11y.
- Operação de CSP/Trusted Types (report-only → enforce) e evidências LGPD/RLS.

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

CSP e Trusted Types
- Report‑Only por 30 dias: cabeçalho `Content-Security-Policy-Report-Only` com `script-src 'strict-dynamic' 'nonce-{RANDOM}'`; `require-trusted-types-for 'script'; trusted-types foundation-ui`.
- Enforcement: mover diretivas para `Content-Security-Policy` e garantir injeção de nonce pelo gateway (NJS) em todas as tags `<script>` do index.html.
- Dev local: plugin Vite injeta nonce e mantém TT em report-only.
- Auditar violações e abrir follow-ups.

LGPD / Evidências RLS
- Seguir `docs/lgpd/rls-evidence.md` para coleta de evidências (políticas e testes de isolamento, pgcrypto em campos sensíveis, masking em logs/telemetria).
- Validar que endpoints expostos ao frontend respeitam RLS e não vazam dados entre tenants.

Pontos de Contato
- Frontend Foundation Guild — governança UI/Storybook/Tokens.
- SRE — SLO, budgets e incidentes de performance.
- DS Guild — tokens multi-tenant e acessibilidade.
