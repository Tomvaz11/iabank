# Runbook seed_data (threat model e operacao)

- **Escopo**: seeds baseline/carga/DR e endpoint `/api/v1/seed-profiles/validate` em ambientes dev/homolog/staging/perf. Reutiliza manifestos v1, RBAC/ABAC minimo e WORM/OTEL fail-close.
- **Owners**: seed platform (@seed-admins), SRE (@sre-seeds), Seguranca (@security-lgpd).
- **Artefatos canonicos**: `contracts/seed-data.openapi.yaml`, `contracts/seed-profile.schema.json`, `configs/finops/seed-data.cost-model.yaml`, `docs/compliance/ropa/seed-data.md`, `observabilidade/k6/seed-data-smoke.js`.

## Threat model (STRIDE/LINDDUN resumido)

| Ameaca | Superficie | Mitigacao | Owner |
| --- | --- | --- | --- |
| Spoofing/repudio | API/CLI sem RBAC/ABAC | `SeedPreflightService` exige roles `seed-runner|seed-admin`, ambientes permitidos e Problem Details 403. Auditoria com fingerprints, Idempotency-Key e RateLimit-* obrigatorios. | seed platform |
| Tampering | Manifesto ou hash divergente | Hash `integrity.manifest_hash` e schema v1; preflight fail-close; WORM assinado com verificacao de integridade. | SRE |
| Information disclosure (LINDDUN Linkability/Identifiability) | PII em factories/logs | Vault Transit FPE + pgcrypto; logs/OTEL com redacao; stubs Pact/Prism bloqueiam outbound real. | Seguranca |
| Denial of service | Fila sem TTL ou sem cap global | `SeedQueueService` + `SeedRunService` (cap global/TTL 5m); Problem Details 409/429 + Retry-After; k6 thresholds p95/p99 + budget. | SRE |
| Elevation of privilege | Uso de role incorreta ou off-peak desabilitado | RBAC/ABAC estrito, window off-peak no manifesto; `check-migrations.sh` barra alteracoes destrutivas; preflight Vault/WORM exige dependencia ativa. | seed platform |

Criterios de sucesso: zero vazamento cross-tenant, nenhum outbound real, RPO<=5m/RTO<=60m em staging/perf, checklist PII/WORM aprovado e cost-model alinhado (budget alert em 80%, abort em 100%).

## Operacao e gates
- **Preflight**: `backend.apps.tenancy.services.seed_preflight.SeedPreflightService` (CLI/API) bloqueia falta de Vault/WORM/RBAC/ambiente. Variaveis exigidas: `VAULT_TRANSIT_PATH`, `SEEDS_WORM_BUCKET`, `SEEDS_WORM_ROLE_ARN`, `SEEDS_WORM_KMS_KEY_ID`, `SEEDS_WORM_RETENTION_DAYS>=1855` (30 dias + 5 anos).
- **Manifesto obrigatório**: CLI/API falham em `422` sem manifesto válido, sem `integrity.manifest_hash` ou sem `reference_datetime` (ISO 8601 UTC). Não há manifesto default; `manifest_path` deve apontar para `configs/seed_profiles/<env>/<tenant>.yaml`. Off-peak sempre é imposto (sem override).
- **Integrações externas**: `backend.apps.tenancy.services.seed_integrations.SeedIntegrationService` recusa hosts fora da allowlist (`localhost/127.0.0.1/prism/pact/stub`); configure `SEED_STUB_BASE` ou URLs explícitas (`SEED_KYC_URL`, `SEED_ANTIFRAUDE_URL`, `SEED_PAGAMENTOS_URL`, `SEED_NOTIFICACOES_URL`) para os Pact stubs (`contracts/pacts/*.json`). Qualquer endpoint real retorna Problem Details `external_calls_blocked`.
- **CI/Argo**: rodar `scripts/ci/check-migrations.sh` (expand/contract sem DROP) e `scripts/ci/validate-finops.sh` (schema/caps FinOps). K6 smoke: `observabilidade/k6/seed-data-smoke.js` com thresholds p95<5s, p99<7s, erro<2%.
- **IaC/OPA (T083)**: validar `infra/terraform/seed-data` com `scripts/ci/validate-opa.sh` (terraform fmt/init/validate + `opa test` usando fixtures em `infra/opa/seed-data/fixtures/plan.json`). Bucket WORM, Redis (fila curta) e Transit são obrigatórios e precisam das tags/retencao definidas na policy.
- **GitOps Argo (T084)**: app `seed-data-pipeline` (namespace `argocd`, caminho `infra/argocd/seed-data/`) sincroniza recursos em `seed-data/` com janela off-peak 02:00–05:00 UTC e cronjob de drift/rollback. Configure o token `argocd-seed-data-token` e ajuste `off_peak_window_utc` na ConfigMap `seed-data-release-policy` se necessário. Para validar sintaxe localmente, use `kubectl kustomize infra/argocd/seed-data` (ou `kustomize build`) — exige binário `kubectl` disponível.
- **Evidencias**: relatorio WORM com manifesto, hash, SLO/FinOps, uso de rate-limit, Problem Details e assinatura verificada. Referenciar ROPA em `docs/compliance/ropa/seed-data.md`.
- **Resposta**: falha de Vault/WORM/OTEL retorna 503/telemetry_unavailable e bloqueia execucao; acionar incident-response quando detectada PII real ou vazamento cross-tenant.
- **API cancelamento**: `/api/v1/seed-runs/{id}/cancel` exige `If-Match`; ausência retorna `428 Precondition Required`, mismatch retorna `412`. Reforça governança/idempotência em concorrência.
