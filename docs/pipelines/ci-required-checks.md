# Pipeline: CI Required Checks

Reflete os gates constitucionais (v5.1.1) e ADRs 008–012.

## Jobs Obrigatórios
1. **tests-unit**: `pytest` (preferencialmente sharded com `xdist`), cobertura ≥85%.
2. **tests-integration**: inclui cenários de RLS (`CREATE POLICY` + enforcement) e `factory-boy`.
3. **tests-contract**: Spectral, openapi-diff, Pact (`ci/contracts.yml`) com cenários de idempotência e concorrência.
4. **tests-security**: SAST, DAST, SCA, verificação de pgcrypto/mascaramento (scripts do ADR-010).
5. **tests-performance**: k6 com thresholds definidos nos SLOs aprovados (documentar no repositório de SLOs/SLA) e revisados semestralmente.
6. **build-sbom**: Gera CycloneDX/SPDX.
7. **iac-policy**: Terraform plan + OPA/Gatekeeper.
8. **finops-tags**: Script para validar tagging obrigatório (Artigo XVI).

## Automação Pendente
- Revisar periodicamente os scripts em `scripts/` conforme o amadurecimento dos serviços.
- Ajustar workflows (`.github/workflows/*.yml`) quando a infraestrutura real for integrada.
- Atualizar o catálogo de SLO/thresholds em `docs/slo/` sempre que novos domínios surgirem.

## Estratégia de Execução
- Habilitar paralelização (e.g., `pytest-xdist`, `k6` em múltiplos VUs) para manter SLAs de pipeline < 15 min.
- Usar filtros de caminho/monorepo para executar somente jobs impactados por cada PR.
- Monitorar tempos de execução e ajustar limites de cobertura/thresholds via ADR antes de qualquer alteração.
- Registrar métricas de sucesso dos jobs para alimentar dashboards DORA/SLO automaticamente.

## Saídas
- Artefatos devem ser enviados para armazenamento WORM.
- Resultados agregados alimentam os dashboards DORA/SLO.
