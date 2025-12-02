# Plano de Validação E2E — F‑11 Seeds, Dados de Teste e Factories

Este plano valida ponta‑a‑ponta a automação de seeds/factories (baseline/carga/DR/canary) com manifestos v1, APIs `/api/v1/seed-profiles/validate` e `/api/v1/seed-runs*`, PII mascarada (Vault Transit), WORM, rate limit/budgets e governança de contratos. Alinha os gates locais aos do CI/GitOps.

## Objetivos
- Reproduzir localmente os gates essenciais de F‑11: manifestos, contratos, PII/RLS, idempotência/locks, WORM, OTEL e budgets (FinOps).
- Garantir que seeds/factories são determinísticas, 100% sintéticas e aderentes aos contratos `/api/v1`.
- Produzir evidências (logs/artefatos) equivalentes ao pipeline CI/CD e Argo CD.

## Escopo e Origem (F‑11 — Seeds Automation)
- Cobre exclusivamente a Feature F‑11 (Automação de seeds/factories). Não aborda F‑01…F‑09/F‑10.
- Artefatos de origem: `specs/003-seed-data-automation/{spec.md,plan.md,quickstart.md,tasks.md,research.md,data-model.md,clarifications-archive.md}`, contratos em `specs/003-seed-data-automation/contracts`, schema em `contracts/seed-profile.schema.json`.
- Infra/Governança: Terraform/OPA/Argo em `infra/terraform/seed-data`, `infra/opa/seed-data`, `infra/argocd/seed-data`.
- Manifestos v1: `configs/seed_profiles/<env>/<tenant>.yaml`; cost model FinOps: `configs/finops/seed-data.cost-model.yaml`.
- Fora do escopo: qualquer snapshot/dump de produção; execuções em ambiente `prod` (proibido).

## Pré‑requisitos
- Node.js 20 + pnpm 9; Python 3.11 + Poetry 1.8.3.
- Docker/Compose; Redis/Postgres locais (pgcrypto/RLS ativos).
- Terraform CLI instalado no PATH (usado em `scripts/ci/validate-opa.sh`).
- Vault Transit acessível; dry-run falha se dependências de Vault/WORM estiverem ausentes (fail-close).
- Stubs Pact/Prism para integrações externas (ports 4010/4011/4012).
- Variáveis sensíveis carregadas (não logar segredos): `VAULT_TRANSIT_PATH`, `SEEDS_WORM_*`.

## Fase 0 — Infra local (necessária para APIs)
```bash
docker compose -f infra/docker-compose.foundation.yml up -d postgres redis backend
```
Critérios: containers healthy; backend responde em `http://localhost:8000/metrics`; backend iniciado com `configs` montado em read‑only e envs de Vault/WORM/FinOps presentes (mesmo que stub para dry-run).
Artefatos: logs do compose (se necessário).

## Permissões/Recursos
- Rede externa habilitada para `pnpm/Poetry`, `docker pull`, downloads de OPA se necessário.
- Ações destrutivas (rm/prune/reset) proibidas; WORM exige retenção/lock.
- Segredos jamais em logs; Chromatic não se aplica aqui.

## Fase 1 — Guardrails e OPA/Terraform (fail-close)
```bash
scripts/ci/seed-guardrails.sh              # bloqueia env=prod, dumps/snapshots
VALIDATE_OPA_REQUIRE_PLAN=1 scripts/ci/validate-opa.sh  # Terraform seed-data + OPA (infra/opa/seed-data)
```
Critérios: sem referências a prod/snapshots; OPA sem denies para bucket WORM, fila curta, Vault Transit. Para validação completa não aceitar fallback de fixture: `terraform plan` real deve ser executado com credenciais válidas para gerar o plano consumido pelo OPA.
Artefatos: logs do script; fixtures OPA em `infra/opa/seed-data/fixtures/plan.json`.

## Fase 2 — Dependências (Node/Python)
```bash
pnpm install
python -m pip install -U pip && pip install "poetry==1.8.3"
poetry install --with dev --sync --no-interaction --no-ansi
```
Critérios: toolchain pronto (`node -v`, `pnpm -v`, `poetry --version`), env Python funcional.

## Fase 3 — Lint/Contratos/Schema
```bash
scripts/ci/seed-data-lint.sh               # Spectral + oasdiff + schema JSON
scripts/ci/validate-seed-contracts.sh      # stubs Pact 2xx/429 + checklist WORM
node scripts/ci/seed-manifest-validate.js --schema contracts/seed-profile.schema.json --root .
```
Critérios: nenhum lint/diff breaking; schema válido; manifestos/caps Q11 válidos; stubs Pact com 2xx/429; checklist WORM com itens obrigatórios.
Artefatos: logs de lint/diff; validação de manifestos.

## Fase 4 — Qualidade Backend (RLS/PII/Factories)
```bash
poetry run ruff check .
poetry run pytest -q
poetry run python scripts/ci/check_python_complexity.py
poetry run python scripts/security/check_pgcrypto.py
bash scripts/security/check_pgcrypto.sh backend/
```
Critérios: Ruff sem erros; pytest verde (inclui RLS, Problem Details, factories, rate-limit); cc ≤ 10; pgcrypto/PII ok.
Artefatos: logs de testes/lint/complexidade.

## Fase 5 — Dry-run determinístico (CI/PR)
```bash
SIMULATE_TELEMETRY_FAILURE=0 scripts/ci/seed-data-dry-run.sh
```
- Usa manifesto default `configs/seed_profiles/staging/tenant-a.yaml` (pode sobrepor via env `SEED_PROFILE_PATH`, `SEED_TENANT_ID`, `SEED_ENVIRONMENT`, `SEED_MODE`, `SEED_REFERENCE_DATETIME`).
- Se variáveis de Vault/WORM ausentes, o script falha (fail-close) para evitar “green” falso.
Critérios: exit 0; sem drift de `reference_datetime`; caps Q11 respeitados; sem falha OTEL/Sentry/WORM (ou stub).
Artefatos: log com Idempotency-Key e manifesto usado.

## Fase 6 — API Manifesto (`/seed-profiles/validate`)
```bash
curl -X POST http://localhost:8000/api/v1/seed-profiles/validate \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-a" \
  -H "X-Environment: staging" \
  -H "Idempotency-Key: validate-$(uuidgen)" \
  -d "$(yq -o=json '{\"manifest\": .}' < configs/seed_profiles/staging/tenant-a.yaml)" -i
```
Critérios: 200 com `valid=true` + `RateLimit-*`; 422 Problem Details para schema/versão inválida ou ausência do wrapper `manifest`; 429 com `Retry-After` em rate-limit; replays idempotentes retornam mesma resposta.
Artefatos: resposta cURL/logs.

## Fase 7 — API Seed Runs (`/seed-runs*`)
```bash
# criar
curl -X POST http://localhost:8000/api/v1/seed-runs \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-a" \
  -H "X-Environment: staging" \
  -H "Idempotency-Key: run-$(uuidgen)" \
  -d '{"manifest_path":"configs/seed_profiles/staging/tenant-a.yaml","mode":"baseline","dry_run":true}' -i
# consultar
curl -X GET http://localhost:8000/api/v1/seed-runs/<id> -H "If-None-Match: <etag>" -i
# cancelar
curl -X POST http://localhost:8000/api/v1/seed-runs/<id>/cancel -H "If-Match: <etag>" -H "Idempotency-Key: cancel-$(uuidgen)" -i
```
Critérios: 201 com `seed_run_id`, `ETag`, `RateLimit-*`; GET 200/304 conforme ETag; cancel 202; 409/429 previsíveis em lock/rate-limit/budget.
Artefatos: logs/respostas.

## Fase 8 — Execução Carga/DR (staging/perf dedicados)
```bash
poetry run python backend/manage.py seed_data \
  --tenant-id <UUID> \
  --environment perf \
  --mode dr \
  --manifest-path configs/seed_profiles/perf/tenant-a-dr.yaml \
  --idempotency-key dr-$(uuidgen)
```
Critérios: janelas off-peak respeitadas; locks por tenant/ambiente OK; caps/rate-limit/budget não estouram; checkpoints limpos em reexecução; WORM escrito e verificado; redaction de PII mantida. Para DR/carga a validação só é completa sem `--dry-run`, com `worm_proof` real no manifesto, ambiente/headers coerentes (`environment=perf|staging`) e sem relaxar `SEED_ALLOWED_ENVIRONMENTS`. Manifestos de perf devem residir em `configs/seed_profiles/perf/*` para evitar `gitops_drift`.
Artefatos: relatório WORM assinado, logs OTEL/Sentry sem falha, checkpoints.

## Fase 9 — Observabilidade e WORM
- Dashboards/logs: `observabilidade/dashboards/seed-data.json`; checar spans/métricas/logs com labels `tenant_id/environment/seed_run_id` e `pii_redacted=true`.
- Checklist WORM: `observabilidade/checklists/seed-worm-checklist.json` (itens `pii_masked`, `rls_enforced`, `contracts_aligned`, `idempotency_reused`, `rate_limit_respected`, `slo_met`).
- Falha de OTEL/Sentry ou WORM → run marcado failed; não promover.
Critérios adicionais para completar validação: WORM com retenção mínima aplicada e prova assinada (não stub); spans/métricas/logs exportados com labels corretas; coleta dos artefatos gerados pelo exporter/collector.
Artefatos: relatório WORM (retention ≥ 365 dias em staging/perf), logs de export.

## Fase 10 — Segurança (SAST/SCA/DAST + PII)
```bash
bash scripts/security/run_sast.sh
poetry self add poetry-plugin-export || true
poetry run bash scripts/security/run_python_sca.sh all
pnpm audit:frontend || true                 # tooling JS
ZAP_BASELINE_TARGET=http://127.0.0.1:8000/metrics ZAP_SKIP_SERVER_START=1 \
  bash scripts/security/run_dast.sh
```
Critérios: Semgrep sem High/Critical; SCA sem CVEs críticos (ou pipeline bloqueia); DAST sem 5xx/achados críticos; pgcrypto/PII verificados na Fase 4.
Artefatos: `artifacts/python-sca/*`, logs Semgrep/DAST.

## Fase 11 — Performance e FinOps
- Perf smoke (se aplicável): ajustar cenários k6 para seeds ou rodar gate leve de throughput
```bash
FOUNDATION_PERF_MODE=local FOUNDATION_PERF_SKIP_BUILD=true FOUNDATION_PERF_VUS=1 pnpm perf:smoke:ci
```
- Orçamentos: seguir `configs/finops/seed-data.cost-model.yaml`; abortar em ≥100% do budget/error budget; alertar em 80%.
Critérios: p95/p99 dentro do manifesto; consumo de budget ≤ 100%; rate-limit não estourado; OTEL exporter ativo para não gerar alertas de throughput ausente.
Artefatos: `artifacts/perf/k6-smoke.json` (se gerado), relatórios/metrics FinOps (ex.: `artifacts/seed-finops.json` se aplicável).

## Fase 12 — Pre‑commit (opcional)
```bash
poetry run pre-commit install || true
poetry run pre-commit run --all-files --show-diff-on-failure
```
Critérios: hooks verdes (Ruff/ESLint convergentes com fases anteriores).

## Checklist de Evidências
- Contratos/Schema: lint/diff Spectral/oasdiff, schema JSON ok, stubs Pact 2xx/429.
- Manifestos: validação JSON Schema + caps Q11; execuções com `reference_datetime` consistente.
- Backend: Ruff/pytest/complexidade; pgcrypto/PII; coverage ≥ 85% (via pytest config).
- Seeds: dry-run CI (exit 0), execuções API/CLI com RateLimit/Idempotency/ETag; locks e checkpoints OK.
- Carga/DR: respeitou off-peak, caps/rate-limit/budget; relatório WORM assinado (real, não stub).
- Observabilidade: spans/métricas/logs rotulados; sem falha OTEL/Sentry/redaction; exporter alcançável.
- Segurança: SAST/SCA/DAST sem High/Critical; guardrails anti-prod/snapshots.
- FinOps/Perf: budgets dentro do cost model; artefatos de perf (se aplicável).
- IaC/OPA: validate-opa sem denies para WORM/fila/Vault; Argo configs presentes (drift cron).

## Notas
- Proibido ambiente `prod` em manifestos; qualquer referência falha em guardrail.
- Dados sempre sintéticos; snapshots/dumps reais são bloqueados.
- `reference_datetime` é breaking: drift exige limpar checkpoints/datasets antes de reseed.
- `canary` só quando `mode=canary`; ausente nos demais modos.
- Falha de WORM ou OTEL/Sentry deve impedir promoção/aceite do run.
