# Pipeline: CI Required Checks

Reflete os gates constitucionais (v5.2.0) e ADRs 008–012.

## Jobs Obrigatórios
1. **tests-unit**: `pytest` (preferencialmente sharded com `xdist`), cobertura ≥85%.
2. **tests-integration**: inclui cenários de RLS (`CREATE POLICY` + enforcement) e `factory-boy`.
3. **tests-contract**: Spectral, openapi-diff, Pact (`ci/contracts.yml`) com cenários de idempotência e concorrência.
4. **tests-security**: SAST, DAST, SCA, verificação de pgcrypto/mascaramento (scripts do ADR-010).
5. **tests-performance**: k6 com thresholds definidos nos SLOs aprovados (documentar no repositório de SLOs/SLA) e revisados semestralmente.
6. **build-sbom**: Gera CycloneDX/SPDX.
7. **iac-policy**: Terraform plan + OPA/Gatekeeper.
8. **finops-tags**: Script para validar tagging obrigatório (Artigo XVI).
9. **complexity-gate**: Radon cc ≤ 10 (Python) usando `scripts/ci/check_python_complexity.py` e allowlist controlado.

## Automação Pendente
- Revisar periodicamente os scripts em `scripts/` conforme o amadurecimento dos serviços.
- Ajustar workflows (`.github/workflows/*.yml`) quando a infraestrutura real for integrada.
- Atualizar o catálogo de SLO/thresholds em `docs/slo/` sempre que novos domínios surgirem.

## Estratégia de Execução
- Habilitar paralelização (e.g., `pytest-xdist`, `k6` em múltiplos VUs) para manter SLAs de pipeline < 15 min.
- Usar filtros de caminho/monorepo para executar somente jobs impactados por cada PR.
- Monitorar tempos de execução e ajustar limites de cobertura/thresholds via ADR antes de qualquer alteração.
- Registrar métricas de sucesso dos jobs para alimentar dashboards DORA/SLO automaticamente.

## Prova de TDD (Art. III)
- PRs DEVEM evidenciar “vermelho → verde” para mudanças de código:
  - Inclua no corpo do PR os commits/links para: (1) estado vermelho (testes falhando) e (2) estado verde (após implementação).
  - Alternativamente, anexe logs do job ‘test’ que mostrem a falha esperada anterior à correção.
- Exceções pontuais (hotfix de infraestrutura, ajustes em scripts/CI ou documentação) DEVEM registrar justificativa no PR.

## Complexidade (Radon)
- O job `Radon complexity gate` no workflow `frontend-foundation.yml` executa `scripts/ci/check_python_complexity.py` (limite cc ≤ 10; allowlist em `scripts/ci/complexity_allowlist.json`).
- Localmente, rode: `poetry run python scripts/ci/check_python_complexity.py`.

## Saídas
- Artefatos devem ser enviados para armazenamento WORM.
- Resultados agregados alimentam os dashboards DORA/SLO.

## Contextos de proteção (GitHub Required Checks)
Estes são os contextos atualmente exigidos na proteção da branch `main` (Branch protection rules). Mantemos a lista aqui para referência rápida e auditoria:
- Lint
- Vitest
- Contracts (Spectral, OpenAPI Diff, Pact)
- Visual & Accessibility Gates
- Performance Budgets
- Security Checks
- Threat Model Lint
- CI Outage Guard
- CI Diagnostics

Notas de governança relacionadas:
- Merge: squash-only, com exclusão de branch ao mesclar.
- Histórico linear: habilitado.
- Resolução de conversas antes do merge: habilitada.
- Aprovações obrigatórias: 0 (atual) — quando houver equipe, migrar para 1–2 aprovações e, se desejado, exigir review de CODEOWNERS.
