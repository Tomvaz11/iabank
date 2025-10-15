# Quickstart — F-10 Fundação Frontend FSD e UI Compartilhada

## 1. Pré-requisitos
- Node.js 20.x, pnpm 9.x instalados.
- Python 3.12 + Poetry para utilitários CLI.
- Docker/Docker Compose para stack backend + Redis + PostgreSQL.
- Acesso ao Vault (`vault login`) e às chaves em `kv/foundation/frontend`:
  - `cspNonceSecret` → exportar em dev como `FOUNDATION_CSP_NONCE`
  - `trustedTypesPolicy` → exportar em dev como `FOUNDATION_TRUSTED_TYPES_POLICY`
  - `pgcryptoKey` → exportar em dev como `FOUNDATION_PGCRYPTO_KEY`
  Observação: a nomenclatura acima alinha com o plano (plan.md: "Vault Integration").

## 2. Inicialização do Monorepo
```bash
git checkout 002-f-10-fundacao
pnpm install
poetry install --only scaffolding
```

## 3. Provisionar Infra Local
```bash
docker compose -f infra/docker-compose.foundation.yml up -d
```
- Serviços: `backend`, `frontend`, `postgres`, `redis`, `otel-collector`.
- Roda migrações iniciais, habilita RLS e carrega tenants demo (`tenant-alfa`, `tenant-beta`).

## 4. Executar Scaffolding de Feature
```bash
pnpm foundation:scaffold feature loan-tracking \
  --tenant tenant-alfa \
  --tags @SC-001,@SC-003 \
  --idempotency $(uuidgen)
```
- Gera slices `app/pages/features/entities/shared`.
- Atualiza roteador multi-tenant e registra `FeatureTemplateRegistration`.
- Executa lint FSD (`pnpm lint:fsd`) e Vitest inicial (falha esperada até implementação).

## 5. Sincronizar Tokens Tailwind
```bash
pnpm foundation:tokens pull --tenant tenant-alfa
pnpm foundation:tokens build
```
- Fonte de verdade: endpoint `GET /api/v1/tenants/{tenantId}/themes/current` (OpenAPI `specs/002-f-10-fundacao/contracts/frontend-foundation.yaml`).
- Converte `docs/design-system/tokens.md` em JSON por tenant para fallback/local.
- Gera `frontend/src/shared/config/theme/tenants.ts` e `src/shared/ui/tokens.css`.
- Atualiza Storybook com variações multi-tenant.

## 6. Rodar Storybook + Chromatic Local
```bash
pnpm storybook
pnpm chromatic --project-token $CHROMATIC_PROJECT_TOKEN --exit-zero-on-changes
```
- Verifique cobertura >=95% na saída do Chromatic.
- Corrija violações do axe-core antes do merge.
 - Em ambiente local sem subdomínio, o tenant padrão aplicado às stories é `tenant-default` (ver contrato: `TenantHeaderOptional`).

## 7. Validar Observabilidade
```bash
pnpm foundation:otel verify --tenant tenant-alfa
```
- Gera trace com baggage `tenant_id`, valida mascaramento de PII e export para collector.
 - Configure variáveis OTEL locais, por exemplo:
   - `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`
   - `OTEL_SERVICE_NAME=frontend-foundation`
   - `OTEL_RESOURCE_ATTRIBUTES=deployment.environment=local,service.namespace=iabank,service.version=0.0.0`

## 8. Executar Pipelines Locais
```bash
pnpm lint
pnpm test
pnpm pact:verify
pnpm lighthouse --config frontend/lighthouse.config.mjs
pnpm k6 run tests/performance/frontend-smoke.js
```
- Certifique-se de cobertura ≥85% e budgets Lighthouse (LCP ≤ 2.5s, TTI ≤ 3.5s).
 - Budgets e racional estão descritos em `docs/adr/adr-perf-front.md`.

## 9. Atualizar Contratos
```bash
pnpm openapi:pull
pnpm openapi:diff
pnpm openapi:generate
pnpm pact:publish
```
- Atualiza `contracts/api.yaml` (caminho relativo ao repositório).
- Use `specs/002-f-10-fundacao/contracts/frontend-foundation.yaml` como contrato de apoio desta feature na etapa de planejamento. A publicação/canonização para `contracts/` será definida em `/speckit.tasks`.
- Publica Pact no broker (URL configurada via Vault).

## 10. Checklist antes do PR
- [ ] Tags `@SC-00x` presentes em commits/testes.
- [ ] `pnpm lint`, `pnpm test`, `pnpm chromatic`, `pnpm lighthouse` verdes.
- [ ] CSP e Trusted Types sem violações (modo report-only acompanhe logs).
- [ ] `specs/002-f-10-fundacao/contracts/frontend-foundation.yaml` validado e consistente com `contracts/api.yaml` (quando aplicável).
- [ ] `docs/runbooks/frontend-foundation.md` atualizado com resultados.

## 11. GitOps e Deploy
- Abra PR com rótulo `foundation`.
- Pipelines GitHub Actions executam gates obrigatórios.
- Argo CD sincroniza manifests `infra/argocd/frontend-foundation`.
- Após deploy, verifique dashboards SC-001–SC-005 e feche a tarefa correspondente em `/specs/002-f-10-fundacao/tasks.md`.
