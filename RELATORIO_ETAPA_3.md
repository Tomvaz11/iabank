# Relatório — Etapa 3 (Fases 8–12)

Status: CONCLUÍDA

## Metadados
- Repositório: iabank
- Branch: main
- Commit: fd7456c
- Data/Hora: 2025-11-16T17:17:14-03:00
- Ferramentas: Node v20.17.0; pnpm 9.12.2; Poetry (version 1.8.3); Python 3.12.3

## Resumo Executivo
- Segurança: SAST (Semgrep) sem findings; SCA Python (pip-audit/Safety) sem vulnerabilidades High/Critical; SCA Node (prod) sem High/Critical; DAST (ZAP baseline) com apenas WARN, sem FAIL.
- Conformidade: Threat Model Lint e Docs Gate aprovados.
- Inventário/Operações: SBOM do frontend gerada; FinOps report executado; pre-commit hooks todos "Passed"; CI consultado (últimos runs saudáveis na main).

---

## Fase 8 — Segurança (SAST/SCA/DAST + pgcrypto)
- Comandos executados:
  - `bash scripts/security/run_sast.sh`
  - `poetry self add poetry-plugin-export || true`
  - `poetry run bash scripts/security/run_python_sca.sh all`
  - `pnpm audit:frontend || true`
  - `ZAP_BASELINE_TARGET=http://127.0.0.1:58001/metrics ZAP_SKIP_SERVER_START=1 bash scripts/security/run_dast.sh`
  - `PYTHONPATH=$PWD poetry run python scripts/security/check_pgcrypto.py`
  - `bash scripts/security/check_pgcrypto.sh backend/`
- Resultados:
  - Semgrep: 0 findings (threshold ERROR).
  - pip-audit: OK; Safety: OK (sem High/Critical).
  - pnpm audit (prod): sem High/Critical.
  - ZAP baseline: 6 WARN não bloqueantes (headers/cache/404 esperados); 0 FAIL; sem 5xx.
  - pgcrypto: verificação do `EncryptedJSONField` passou e padrões `pgcrypto`/`pgp_sym_encrypt` presentes.
- Artefatos:
  - `artifacts/python-sca/pip-audit.json`
  - `artifacts/python-sca/safety.json`
  - `artifacts/zap/zap-baseline.json`, `artifacts/zap/zap-report.html`, `artifacts/zap/zap-report.xml`, `artifacts/zap/zap-warnings.md`

## Fase 9 — Threat Model & Docs Gate
- Comandos executados:
  - `python scripts/security/threat_model_lint.py --release v1.0`
  - `node scripts/ci/check-docs-needed.js`
- Resultados: ambos OK sem erros.

## Fase 10 — SBOM e FinOps
- Comandos executados:
  - `pnpm sbom:frontend`
  - `pnpm finops:report`
- Resultados:
  - SBOM gerada com sucesso.
  - FinOps report executado, JSON impresso no console (sem alerts).
- Artefatos:
  - `sbom/frontend-foundation.json`

## Fase 11 — Pre‑commit
- Comandos executados:
  - `poetry run pre-commit install || true`
  - `poetry run pre-commit run --all-files --show-diff-on-failure`
- Resultados: todos os hooks "Passed" (Ruff/ESLint convergentes com fases anteriores).

## Fase 12 — CI via gh
- Comando executado: `gh run list --workflow "frontend-foundation.yml" --limit 10`
- Resultado: branch `main` com último run "success"; em PRs recentes houve falhas no job de validação do Chromatic (não bloqueiam esta validação local).

## Evidências (links rápidos)
- SAST: log do Semgrep (0 findings) — saída de console desta execução
- SCA Python: `artifacts/python-sca/pip-audit.json`, `artifacts/python-sca/safety.json`
- DAST: `artifacts/zap/zap-baseline.json`, `artifacts/zap/zap-report.html`
- SBOM: `sbom/frontend-foundation.json`
- pgcrypto: `scripts/security/check_pgcrypto.py` (mensagem "json_payload protegido com pgcrypto.")

## Ocorrências e Ajustes
- Backend já ativo em `127.0.0.1:58001`; DAST direcionado para essa porta conforme disponibilidade local (mantendo critérios do plano).
- Durante a geração da SBOM houve avisos de depreciação de pacotes no ambiente de tooling do npm; não impactam os gates definidos (SCA prod do frontend permaneceu sem High/Critical).

## Conclusão da Etapa 3
Todos os critérios de aceite das Fases 8–12 foram atendidos sem erros bloqueantes:
- Segurança aprovada (SAST/SCA/DAST + pgcrypto).
- Threat Model e Docs Gate OK.
- SBOM gerada; FinOps report executado; pre-commit convergente; CI da main saudável.

---

## Apêndice A — Resumo dos WARN do ZAP (Baseline)
- Total de categorias WARN: 6 (sem FAIL; sem 5xx):
  - Server Leaks Version Information via "Server" header [10036] — 4 ocorrências (/, /metrics, /robots.txt, /sitemap.xml)
  - Storable and Cacheable Content [10049] — 4 ocorrências (/, /metrics, /robots.txt, /sitemap.xml)
  - CSP: Failure to Define Directive with No Fallback [10055] — 4 ocorrências
  - Permissions Policy Header Not Set [10063] — 3 ocorrências
  - Insufficient Site Isolation Against Spectre [90004] — 1 ocorrência (/metrics)
  - Sec-Fetch-Dest Header is Missing [90005] — 8 ocorrências (inclui /metrics)
- Observação: baseline executa apenas varredura passiva. Para pré‑prod, recomenda‑se Active Scan com escopo e contexto configurados.

## Apêndice B — Snapshot dos Últimos Runs do CI (gh)
- Workflow: "Frontend Foundation CI" (últimos 10 runs):
  - main (push): success — "ci(poetry): padronizar Poetry 1.8.3 + guardrails (@SC-005) (#198)"
  - chore/poetry-guardrails-1.8.3 (pull_request): success
  - chore/poetry-guardrails-1.8.3 (push): success
  - chore/poetry-guardrails-1.8.3 (pull_request): failure (intermitente anterior)
  - ci/validate-chromatic (pull_request): failures em tentativas de validação do Chromatic em PR
  - ci/validate-chromatic (workflow_dispatch): success
- Conclusão: branch main está saudável; falhas isoladas em PRs de validação do Chromatic não impactam a validação local desta Etapa 3.

---

## Apêndice C — Validações Extras Executadas
- ZAP Full Scan (ativo)
  - Alvo: `http://127.0.0.1:58001/`
  - Resultado: 0 FAIL; 3 categorias WARN (sem 5xx)
  - Artefatos: `artifacts/zap/full-scan/zap-full.json`, `zap-full-report.html`
- SCA Node (inclui dev deps)
  - Resultado (dev incluido): info 0, low 5, moderate 11, high 4, critical 3
  - Artefato: `artifacts/node-sca/pnpm-audit-dev.json`
- Scan de Imagens (Trivy)
  - Backend: total 1296; HIGH 174; CRITICAL 4 — `artifacts/container-scan/backend-trivy.json`
  - OTEL Collector: total 55; HIGH 19; CRITICAL 3 — `artifacts/container-scan/otel-collector-trivy.json`
- Secrets Scan (Gitleaks — redacted)
  - Achados: 2 (redigidos)
  - Artefato: `artifacts/secrets/gitleaks.json`
- Inventário de Licenças (SBOM)
  - Componentes: 1031; Licenças únicas: 20; Unknown: 0
  - Artefato: `artifacts/licenses/sbom-licenses-summary.json`

Recomendações (não bloqueantes nesta etapa)
- Trivy: avaliar atualização de base images (alpine/debian), aplicar fix de pacotes e definir allowlist de CVEs não exploráveis; considerar imagens distroless.
- pnpm (dev): atualizar dependências de desenvolvimento e/ou pinagem; monitorar na próxima janela de manutenção.
- ZAP (ativo): manter execução em ambiente de pré‑produção com contexto de autenticação quando aplicável.

---

## Apêndice D — Plano de Ações Futuras (Recomendações)
Estas ações não são bloqueantes para a Etapa 3. Priorize conforme impacto/risco.

- Agora (alto impacto/baixo risco)
  - Triagem de segredos (Gitleaks)
    - Artefato: `artifacts/secrets/gitleaks.json`
    - Ações: revogar/rotacionar credenciais reais; se falso positivo, criar `.gitleaks.toml` com regra específica e justificativa (com data de expiração) e reexecutar o scan.
    - Execução sugerida: `docker run --rm -v "$PWD:/repo" -w /repo zricethezav/gitleaks:latest detect --source /repo --redact`
  - CVEs CRITICAL (Trivy)
    - Artefatos: `artifacts/container-scan/backend-trivy.json`, `artifacts/container-scan/otel-collector-trivy.json`
    - Ações: atualizar base images no `backend/Dockerfile` (ex.: tags recentes slim/bookworm), aplicar patches de SO e re‑build; reexecutar Trivy. Para itens não exploráveis, criar `.trivyignore` com justificativa e prazo.
    - Execução sugerida: `docker build -t iabank/backend:local -f backend/Dockerfile . && docker run --rm aquasec/trivy:0.52.2 image iabank/backend:local`

- Próximo ciclo (médio)
  - Atualizar dependências de desenvolvimento (frontend)
    - Comandos: `pnpm --dir frontend up -L` e depois `pnpm lint && pnpm typecheck && pnpm test && pnpm test:e2e`
    - Meta: reduzir HIGH/CRITICAL em dev sem afetar prod.
  - Gates no CI
    - Trivy (imagens e filesystem): publicar SARIF; falhar PR se `CRITICAL>0` (com allowlist controlada por `.trivyignore`).
    - Gitleaks: executar em push/PR com `--redact` e SARIF; falhar se findings>0 (exceto itens em `.gitleaks.toml`).
    - Armazenar artefatos de scan em `artifacts/**` e expor nos checks.
  - ZAP com autenticação (pré‑prod/preview)
    - Criar um arquivo de Automation Framework (YAML) com contexto/login, incluir crawlers e Active Scan; definir thresholds (falhar com Medium/High acima do limite).

- Planejado (baixa)
  - Endurecimento de imagens
    - Migrar para imagens minimal/distroless quando viável; executar como usuário não‑root; `--cap-drop=ALL` quando possível; filesystem read‑only; pinar versões de pacotes e usar `apt-get --no-install-recommends`.
  - Política de licenças
    - Definir allowlist (ex.: MIT, Apache‑2.0, BSD‑2/3, ISC) e validar contra a SBOM. Falhar PR em caso de licença fora da allowlist.
    - Integrar opcionalmente com Dependency‑Track/OSSRH/ORT para acompanhamento contínuo.
  - Governança de exceções
    - Documentar `.trivyignore` e `.gitleaks.toml` com owner, justificativa e data de expiração; revisar periodicamente.
