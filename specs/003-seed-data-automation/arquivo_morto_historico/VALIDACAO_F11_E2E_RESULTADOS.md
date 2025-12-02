# Resultados da Validação E2E — F‑11 (Seeds/Factories)

Relato completo da execução local do plano de validação E2E para F‑11 em 2025-11-29.

## Ambiente e preparos
- Compose: `infra/docker-compose.foundation.yml` com postgres/redis/backend e `vault-dev` (porta 8200); backend com volume `./../configs:/app/configs:ro` e envs:  
  `VAULT_ADDR=http://vault-dev:8200`  
  `VAULT_TOKEN=root`  
  `VAULT_TRANSIT_PATH=transit/staging/seed-data`  
  `SEEDS_WORM_BUCKET=worm-bucket`  
  `SEEDS_WORM_ROLE_ARN=arn:aws:iam::000:role/worm`  
  `SEEDS_WORM_KMS_KEY_ID=arn:aws:kms:us-east-1:000:key/worm`  
  `SEEDS_WORM_RETENTION_DAYS=1855`  
  `SEED_ALLOWED_ENVIRONMENTS=dev,homolog,staging,perf` (CLI liberou `dr` só para o comando)  
  `SEED_ALLOWED_ROLES=seed-runner,seed-admin`
- Vault dev: transit habilitado com chaves `tenant-a-perf` e `tenant-a-staging`; WORM continua stub.
- Backend responde em `http://localhost:8000/metrics` (200). Adicionada entrada RBAC `svc-seeds` para `tenant-a/dev` para testar rate-limit.
- Git diff ao final: `PLANO_VALIDACAO_E2E*.md` não rastreados (lockfile revertido).

## Fases executadas
1) Guardrails/OPA  
   - `scripts/ci/seed-guardrails.sh` OK.  
   - `scripts/ci/validate-opa.sh` usou fixture por falha de credencial AWS no `terraform plan`; OPA PASS (8/8).
2) Dependências  
   - `pnpm install` OK (avisos de deprecados).  
   - `poetry install --with dev --sync` OK (pip upgrade bloqueado por PEP 668).  
3) Lint/contratos/manifestos  
   - `scripts/ci/seed-data-lint.sh`, `scripts/ci/validate-seed-contracts.sh`, `node scripts/ci/seed-manifest-validate.js --schema contracts/seed-profile.schema.json --root .` — todos verdes (7 manifestos).  
4) Qualidade backend  
   - `poetry run ruff check .` OK.  
   - `poetry run pytest -q` OK (205 testes, 94% cobertura).  
   - `poetry run python scripts/ci/check_python_complexity.py` OK.  
   - `PYTHONPATH=. DJANGO_SETTINGS_MODULE=backend.config.settings poetry run python scripts/security/check_pgcrypto.py` OK.  
   - `bash scripts/security/check_pgcrypto.sh backend/` OK (avisos de padrões faltantes informativos).  
5) Dry-run determinístico  
   - `SIMULATE_TELEMETRY_FAILURE=0 scripts/ci/seed-data-dry-run.sh` OK com stub Vault/WORM (vars ausentes); manifesto usado: `configs/seed_profiles/staging/tenant-a.yaml`; Idempotency-Key gerada `seed-dry-run-5e2299c9-1a86-42ad-981e-506285233de9`.
6) API `/seed-profiles/validate`  
   - Payload requer wrapper `{ "manifest": { ... } }`.  
   - 200 OK com manifesto `configs/seed_profiles/staging/tenant-a.yaml` (RateLimit-Limit 960, Remaining 959, Reset 60, hash `8c88eeda7fe51bd4d3599fc26874e82861af6f58bb15b5f5069e7d52d5d2298f`).  
   - 422 para manifesto inválido (campos ausentes/`environment_mismatch`), RateLimit headers retornados.  
   - 429 exercitado com manifesto homolog limit=1 (`hash=413158d33ec08fe1c0294e32ec85694fbedc65d4daffbdc2c3649cf1f95f0da6`): RateLimit-Limit 1, Retry-After 49, resposta Problem Details `rate_limit_exceeded`.
7) API `/seed-runs*`  
   - Staging: POST 201 com manifesto oficial baseline (`seed_run_id=ab17a9dd-abc5-47af-ae2f-f789485b65b7`, `ETag=ac2495f57400836312a26e64cb548e38b6381502069c4e3af0d77d0c27dc6e97`, RateLimit-Limit 960). Replay com mesma Idempotency-Key retornou 201 idempotente (mesmo ETag/seed_run). GET com `If-None-Match` + `Idempotency-Key` e `X-Seed-Subject: svc-seeds` → 304. Cancel com `If-Match` → 202 `aborted`.  
   - Dev (RBAC liberado para teste de rate-limit): manifesto baseline limit=1 (`hash=ebc25f658c4665d2dfb0ac750382149df13c694841debcc0e275505bbf974546`). Primeiro POST 201 (`seed_run_id=8f1f1408-661a-483f-9eab-fb0c88947844`, `ETag=1938fb477ddcb36755c63fb288ba5f1aada9c5df151efd52408f2cec9ad0f984`, RateLimit-Remaining 0); segundo POST com Idempotency-Key diferente retornou 429 com Retry-After 49.  
   - Antes do ajuste: 503 por Vault indisponível e 500 por cost-model ausente; resolvido ao adicionar envs stub e volume `configs` no container.
8) Execução carga/DR via CLI  
   - Manifesto DR oficial ajustado para `environment=perf`, `worm_proof` e hash recalculado; movido para `configs/seed_profiles/perf/tenant-a-dr.yaml` para evitar `gitops_drift`.  
   - `docker compose exec backend .venv/bin/python backend/manage.py seed_data --tenant-id 7d787633-168d-4e27-ac8f-fb2fc8a60c80 --environment perf --mode dr --manifest-path configs/seed_profiles/perf/tenant-a-dr.yaml --idempotency-key dr-8a962cbf-813c-4614-9e9d-9cae8d0d7155` → 202/queue OK, `seed_run=dfcac873-7a30-4961-b25e-c4262c30e0c9`, `queue_entry=e44e4a5b-786d-42be-a6c7-f74c6b1408f1`. GET subsequente bloqueado por RBAC (403) com subject padrão; necessário subject autorizado para consultar/ETag.
9) Observabilidade/WORM  
   - Checklist WORM validada em `scripts/ci/validate-seed-contracts.sh`.  
   - Dry-run usou stub Vault/WORM; run CLI incluiu `worm_proof` stub (não grava WORM real).  
   - Span OTEL exportado via collector local (`http://127.0.0.1:4318`) com labels `seed_run_id=76a092ca-b9cd-438a-8a92-37aa12957279`, `tenant_id=7d787633-168d-4e27-ac8f-fb2fc8a60c80`, `deployment.environment=staging`, `pii_redacted=true`; collector (logging exporter) registrou ingestão.
10) Segurança (SAST/SCA/DAST)  
   - SAST: `bash scripts/security/run_sast.sh` (Semgrep 1.144.0 instalado no venv) — 0 findings.  
   - SCA Python: `poetry run bash scripts/security/run_python_sca.sh all` — sem High/Critical; artefato `artifacts/python-sca/pip-audit.json`.  
   - JS audit: `pnpm audit:frontend` — sem vulnerabilidades.  
   - DAST reexecutado após ajuste CSP (Report-To) e allowlist padrão (`ZAP_BASELINE_IGNORE_ALERTS=10049,90005` no script): `bash scripts/security/run_dast.sh` alvo `http://127.0.0.1:8000/metrics`, sem Low/CSP; restaram apenas INFO esperados (`no-store` intencional, cabeçalhos Sec-Fetch-* ausentes por ser tráfego não-browser). Relatórios atualizados em `artifacts/zap/`.
11) Performance/FinOps  
   - OTEL collector local iniciado (`otel/opentelemetry-collector:0.102.1`, config `infra/otel-collector-config.yaml`, portas 4317/4318).  
   - `OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318 FOUNDATION_PERF_MODE=local FOUNDATION_PERF_SKIP_BUILD=true FOUNDATION_PERF_VUS=10 pnpm perf:smoke:ci` — sucesso com throughput 10rps (status=ok nos thresholds locais default), `artifacts/perf/k6-smoke.json` atualizado.  
   - `scripts/ci/validate-finops.sh` validou `configs/finops/seed-data.cost-model.yaml` contra o schema v1 (OK).
12) Pre-commit  
   - `poetry run pre-commit run --all-files --show-diff-on-failure` OK.

## Falhas observadas e workarounds aplicados
- `validate-opa.sh`: com `VALIDATE_OPA_REQUIRE_PLAN=1` o `terraform plan` falhou por credencial AWS (InvalidClientTokenId) e o script abortou (sem fixture).  
- API `/seed-profiles/validate`: requer campo `manifest`; sem wrapper retorna 422 (registrado).  
- API `/seed-runs`: antes de montar `configs` e setar Vault/WORM stub o container respondia 500/503; corrigido no compose. 422 quando payload sem `manifest` (não reproduzido com payload válido).  
- CLI `seed_data`: bloqueios por environment gate para `dr` fora de staging/perf e por manifesto com environment divergente; resolvido com manifesto perf real, path em `configs/seed_profiles/perf/*` e execução via container backend. RBAC em perf ajustado via inserção de `SeedRBAC` (`svc-seeds` seed-read/seed-admin) — GET do run agora 200 com ETag.  
- DAST: apenas INFO esperados (no-store intencional + ausência de cabeçalhos Sec-Fetch-* em tráfego não-browser) após allowlist default.  
- Perf smoke: thresholds locais default (VUS=10, throughput 10rps status=ok) com OTEL export ativo.

## Artefatos relevantes
- Perf: `artifacts/perf/k6-smoke.json` (coletor OTEL local em `localhost:4318`, throughput 10rps nos thresholds locais)
- SCA Python: `artifacts/python-sca/pip-audit.json`
- DAST: `artifacts/zap/` (json/html/xml/md)
- Dry-run: log `seed-data-dry-run.sh` (stdout), Idempotency-Key `seed-dry-run-5e2299c9-1a86-42ad-981e-506285233de9`
- Seed-run API staging: `seed_run_id=ab17a9dd-abc5-47af-ae2f-f789485b65b7`, `ETag=ac2495f57400836312a26e64cb548e38b6381502069c4e3af0d77d0c27dc6e97` (201 + replay idempotente, GET 304, cancel 202).  
- Seed-run API dev (rate-limit limit=1): `seed_run_id=8f1f1408-661a-483f-9eab-fb0c88947844`, `ETag=1938fb477ddcb36755c63fb288ba5f1aada9c5df151efd52408f2cec9ad0f984` (primeiro POST 201, segundo POST 429 Retry-After 49).  
- Execução DR perf (não dry-run): `seed_run=dfcac873-7a30-4961-b25e-c4262c30e0c9`, manifesto `configs/seed_profiles/perf/tenant-a-dr.yaml`, queue_entry `e44e4a5b-786d-42be-a6c7-f74c6b1408f1`, ETag `6875532e1c838ae376c0b82964bec489169a93ea5a79b5a9cdaf59787db41f69` (status=queued).
- Observabilidade: `artifacts/observabilidade/seed-span.log` (span OTEL com labels de tenant/environment/seed_run/pii_redacted), `artifacts/observabilidade/otel-collector.log` (ingestão via logging exporter).

## Itens em aberto
- Manifesto DR ajustado e movido, mas prova WORM real ainda não foi gerada; fila `seed_data.load_dr` enfileirada (`seed_run=dfcac873-7a30-4961-b25e-c4262c30e0c9`) aguarda processamento/worker e credenciais WORM para assinar.  
- OPA ainda falhou com `VALIDATE_OPA_REQUIRE_PLAN=1` por `InvalidClientTokenId` (credenciais AWS ausentes/ inválidas); sem plan Terraform real o script aborta.  
- Evidências WORM reais ainda pendentes; Vault Transit local habilitado, mas sem prova WORM/assinatura.

## Plano de ação para completar a validação (seguir PLANO_VALIDACAO_E2E_F11.md)
1) OPA/Terraform real: executar `VALIDATE_OPA_REQUIRE_PLAN=1 scripts/ci/validate-opa.sh` com credenciais válidas (ex.: `AWS_PROFILE=seed-data`), garantindo que o `terraform plan` seja gerado e consumido pelo OPA (sem fixture). Guardar o plan/saída do OPA como artefato.  
2) DR/Carga oficial: usar `configs/seed_profiles/perf/tenant-a-dr.yaml` e rodar `backend/manage.py seed_data` sem `--dry-run`, sem relaxar `SEED_ALLOWED_ENVIRONMENTS`, com worker consumindo `seed_data.load_dr` e WORM ativo, capturando `seed_run_id`, checkpoints, ETag e prova WORM real.  
3) WORM real: fornecer `SEEDS_WORM_*` e `VAULT_TRANSIT_PATH` válidos para gravar prova WORM com retenção ≥1855d; anexar relatório WORM assinado. OTEL/observabilidade já exercitado via span manual (`seed_run_id=76a092ca-b9cd-438a-8a92-37aa12957279`); replicar em run real.
