# Research — F-10 Fundação Frontend FSD e UI Compartilhada

## 1. FSD Scaffolding and Governance
- **Decision**: Adopt Feature-Sliced Design with enforced layer boundaries (`app → pages → features → entities → shared`), automated scaffolding scripts, and ESLint import rules that block upward imports.
- **Rationale**: Aligns with `BLUEPRINT_ARQUITETURAL.md §4` and Art. I/II, reduces lead time (SC-001), and matches clarifications requiring lint-enforced boundaries.
- **Alternatives considered**: Component-driven folder structure (atomic design) rejected because it weakens vertical slicing and complicates tenant-aware routing; route-based co-location rejected due to lack of shared contract governance.

## 2. TanStack Query Tenant Partitioning
- **Decision**: Standardize TanStack Query keys as `['tenant', tenantId, domain, resource, params]` with cache policies derived from `meta.tags` per clarifications (critical 30s, default 5m).
- **Rationale**: Guarantees tenant isolation (Art. XIII) and fulfills caching policy clarifications while supporting SC-001/SC-002 metrics.
- **Alternatives considered**: Global cache without tenant prefix rejected (risk of cross-tenant bleed); manual fetch hooks rejected (loss of staleTime and retries governance).

## 3. Zustand for Global State
- **Decision**: Use Zustand 4 with typed slices for UX shell (theme, navigation), persisted session, and integration with TanStack Query via `useStoreWithEqualityFn`.
- **Rationale**: Lightweight, tree-shakeable, integrates with hooks, and satisfies requirement for explicit global store without Redux ceremony.
- **Alternatives considered**: Redux Toolkit rejected due to boilerplate and mismatch with blueprint minimalism; React Context-only rejected for performance and lack of middlewares.

## 4. Tailwind CSS + CSS Variables Theming
- **Decision**: Compile tenant token JSON into Tailwind theme extensions and expose runtime CSS variables under `html[data-tenant]`, with hydrate hooks to switch tenants.
- **Rationale**: Meets adicoes_blueprint.md item 13 and `docs/design-system/tokens.md` directives; supports Chromatic snapshots per tenant and WCAG AA validation.
- **Alternatives considered**: Tailwind multi-config per tenant rejected (duplicated build); CSS-in-JS (Emotion) rejected for bundle overhead and noncompliance with blueprint.

## 5. Storybook, Chromatic and Accessibility Gates
- **Decision**: Configure Storybook with multi-tenant stories, Chromatic coverage ≥95%, axe-core WCAG 2.2 AA checks, and integration with Lighthouse for key components.
- **Rationale**: Enforces SC-002/SC-004, provides visual regression guardrails, and aligns with CI gate clarifications (fail-closed on releases).
- **Alternatives considered**: Percy rejected (overlaps Chromatic, lacks tenant theming support); manual screenshot diff rejected (no automation, brittle).

## 6. OpenTelemetry Propagation in SPA
- **Decision**: Initialize OpenTelemetry Web SDK with W3C Trace Context, propagate `tenant_id` via baggage, and mask PII before exporting to collector.
- **Rationale**: Required by Art. VII and clarifications on PII handling; ensures correlation with backend traces and compliance with ADR-012.
- **Alternatives considered**: Custom logging middleware rejected (no standard context propagation); disabling baggage rejected (would block tenant observability).

## 7. CSP, Trusted Types, and PII Controls
- **Decision**: Ship CSP with strict nonce, enforce Trusted Types after 30-day report-only window, and integrate URL/telemetry scanners for PII allowlist enforcement.
- **Rationale**: Satisfies Art. XII, adicoes_blueprint.md item 13, and clarifications on rollout strategy while preventing DOM XSS regressions.
- **Alternatives considered**: Relaxed CSP (self-only) rejected (insufficient protection); deferring Trusted Types indefinitely rejected (violates clarifications and Art. XII).

## 8. Contract-First API Governance
- **Decision**: Maintain OpenAPI 3.1 in `/home/pizzaplanet/meus_projetos/iabank/contracts/api.yaml`, generate TypeScript clients, and pair with Pact contract tests for critical flows.
- **Rationale**: Fulfills Art. XI and clarifications that hybrids (OpenAPI owner = backend, Pact consumer-driven) are mandatory; supports SC-003.
- **Alternatives considered**: GraphQL schema-first rejected (diverges from DRF stack); handwritten clients rejected (error-prone, breaks contract drift detection).

## 9. Async Processing and CI Gates
- **Decision**: Use Celery 5.3 + Redis 7 workers for Chromatic snapshots, Pact stub spins, and Lighthouse budgets; orchestrate via GitHub Actions with Argo CD sync hooks.
- **Rationale**: Provides deterministic CI gates without overloading frontend build job, aligning with Art. IX and GitOps requirements.
- **Alternatives considered**: GitHub-hosted steps only rejected (long wait times, no retry control); RabbitMQ rejected (already standardized on Redis per Art. I).

## 10. RLS and PII Encryption Backing Frontend
- **Decision**: Enforce PostgreSQL RLS policies per tenant on views exposed to SPA and encrypt sensitive columns with pgcrypto; expose only masked fields to UI.
- **Rationale**: Required by Art. XIII and adicoes_blueprint item 5; prevents cross-tenant leaks and supports zero PII incidents (SC-005).
- **Alternatives considered**: Application-layer filtering alone rejected (defense-in-depth gap); field-level encryption libs in app rejected (duplicated effort versus pgcrypto).
