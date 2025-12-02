# Issue 002 — Alinhar fundação frontend ao spec F-10 (tenant, CSP, Chromatic, theming)

## Contexto e motivação

- Durante a checagem de divergências entre o spec `specs/002-f-10-fundacao/spec.md` e o blueprint base, encontramos implementações que seguem decisões mais fracas do blueprint. São pontos sensíveis de multi-tenant, segurança cliente e governança de design system.
- Itens impactados (todos já implementados, mas em linha com o blueprint e não com o spec):
  - **Roteamento multi-tenant via query string**: `RouterProvider` persiste `tenant` em `?tenant=` (`frontend/src/app/providers/router.tsx`) e o job de perf usa essa rota (`.github/workflows/frontend-foundation.yml`, `LIGHTHOUSE_TARGET_URL`). O spec exige derivar o tenant do subdomínio em produção, com fallback por path apenas em dev/local e sem `tenant` como query param em produção (FR-011/FR-011a).
  - **Header de tenant opcional no client**: `listDesignSystemStories` só envia `X-Tenant-Id` se `tenantId` for informado (`frontend/src/shared/api/client.ts`). O spec (FR-005d) obriga `tenant_id` em todas as query keys e headers para evitar vazamento de cache multi-tenant.
  - **Cobertura Chromatic restrita a um tenant**: o job “Validar cobertura visual por tenant” fixa `CHROMATIC_TENANTS: 'tenant-alfa'` (`.github/workflows/frontend-foundation.yml`) e o checker aceita lista reduzida (`frontend/scripts/chromatic/check-coverage.ts`). O spec (FR-003) exige ≥95% para todos os tenants ativos.
  - **CSP/Trusted Types apenas em dev/report-only**: o plugin `foundation-csp-dev` injeta `Content-Security-Policy-Report-Only` e `require-trusted-types-for 'script'` só no modo `serve` (`frontend/vite.csp.middleware.ts`). O spec (FR-009/FR-009a) pede CSP bloqueante em todos os ambientes e rollout de Trusted Types (30 dias em report-only, depois enforce) com validação em CI.
  - **Theming pré-compilado em CSS**: tokens dos tenants estão materializados em `shared/ui/tokens.css` e consumidos pelo Tailwind em build (`frontend/src/styles.css`, `frontend/src/shared/ui/tokens.css`). O spec (FR-004a) exige abordagem híbrida: tokens em JSON carregados em runtime por tenant + overrides via `[data-tenant]`, sem depender de CSS pré-compilado para todos os tenants.
- Por que mudar:
  - **Isolamento e segurança**: evitar tenants em query param e headers opcionais reduz risco de vazamento de cache/trace/log. CSP/Trusted Types bloqueantes mitigam XSS/supply chain no cliente.
  - **Cobertura visual/a11y**: validar todos os tenants previne regressões de tema/contraste.
  - **Operação multi-tenant**: theming híbrido reduz rebuilds, suporta rollouts seguros e não infla o bundle com CSS de todos os tenants.

## Escopo

1) **Roteamento multi-tenant**
   - Ajustar `RouterProvider` para derivar tenant do subdomínio em produção; manter fallback por path em dev/local, sem usar query `tenant` em produção.
   - Garantir `data-tenant` e reset de caches/estado (já existe) continuam funcionando.
   - Atualizar `LIGHTHOUSE_TARGET_URL` (workflow de perf) para rota compatível com o modelo sem query param em produção.

2) **Header/keys obrigatórios de tenant**
   - Tornar obrigatório `X-Tenant-Id` em todas as chamadas (incluindo `listDesignSystemStories`).
   - Validar que todas as query keys incluem `tenant_id` (TanStack Query) e adicionar teste/lint se faltar.

3) **Cobertura Chromatic por todos os tenants**
   - Atualizar workflow para `CHROMATIC_TENANTS` abranger todos os tenants ativos.
   - Ajustar `frontend/scripts/chromatic/check-coverage.ts` para falhar se cobertura por tenant ficar <95% ou se faltar tenant esperado.

4) **CSP e Trusted Types bloqueantes**
   - Aplicar CSP em modo bloqueante (não apenas report-only) nos builds/preview, com nonce/hash.
   - Implementar rollout de Trusted Types: 30 dias report-only + migração de sinks, depois enforce; validar em CI.
   - Adicionar testes automatizados/linters de CSP/TT se necessário.

5) **Theming híbrido por tenant**
   - Migrar tokens para JSON carregado em runtime por tenant + overrides via `[data-tenant]` (bundle único), mantendo Tailwind para tokens semânticos compilados.
   - Evitar materializar todos os tokens em CSS estático; garantir carregamento lazy e cache seguro por tenant.

## Checklist de entrega

- [ ] Roteamento: subdomínio em prod, fallback por path só em dev/local; remover dependência de `?tenant=` em produção; ajustar workflow de perf.
- [ ] Client HTTP: `X-Tenant-Id` sempre presente; query keys sempre com `tenant_id`; testes/lint cobrindo.
- [ ] Chromatic: cobertura ≥95% para todos os tenants ativos; workflow e checker atualizados.
- [ ] CSP/Trusted Types: CSP bloqueante em todos ambientes; rollout TT (report-only → enforce) configurado e validado em CI.
- [ ] Theming: tokens em JSON runtime + overrides via `[data-tenant]`; remover dependência de CSS pré-compilado para todos os tenants; garantir suporte a fallback seguro.
- [ ] Notas de PR/commit citam que eram divergências spec vs blueprint e agora seguem o spec F-10.

## Referências

- Spec: `specs/002-f-10-fundacao/spec.md` — FR-003, FR-004/FR-004a, FR-005d, FR-009/FR-009a, FR-011/FR-011a.
- Blueprint base: `BLUEPRINT_ARQUITETURAL.md` (não força subdomínio, tenant opcional, CSP genérico, theming compilado).
- Adições: `adicoes_blueprint.md` (CSP/Trusted Types, privacidade no front).

## Notas rápidas de teste/validação

- Frontend: `pnpm lint`, `pnpm test:coverage`, `pnpm test:e2e`, `pnpm perf:lighthouse`, `pnpm chromatic:check` (com todos os tenants configurados).
- Validar que CSP/TT estão ativos no build/preview (inspecionar headers e violações no console) e que tenants não aparecem como query param em produção.

## Validação ponta a ponta (pós-implementação)

- **Roteamento**: em prod/staging acessar sem `?tenant` e confirmar resolução por subdomínio; em dev/local usar fallback por path; trocar de tenant e verificar reset do cache (TanStack Query) e estado sensível em Zustand.
- **Headers/keys**: inspecionar chamadas (DevTools ou testes) e confirmar `X-Tenant-Id` + traceparent/tracestate em todas; verificar que query keys incluem `tenant_id` e não há cache cruzado entre tenants.
- **Chromatic**: executar `storybook:build` + `chromatic:check` com `CHROMATIC_TENANTS` cobrindo todos; validar cobertura ≥95% por tenant e ausência de lacunas de stories por tenant.
- **CSP/Trusted Types**: em build/preview, checar headers CSP bloqueante e TT (report-only → enforce após janela); console sem violações; inline scripts sem nonce devem ser bloqueados; rodar testes/linters de CSP/TT se existirem.
- **Theming híbrido**: trocar de tenant sem rebuild, confirmar carregamento de tokens via JSON e aplicação de `[data-tenant]`; bundle não deve conter CSS de todos os tenants; fallback seguro para tenant inválido.
- **Regressão geral**: `pnpm lint`, `pnpm test:coverage`, `pnpm test:e2e`, `pnpm perf:lighthouse` e smoke dos clientes HTTP.
