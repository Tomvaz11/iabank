# ADR — Performance Frontend (Lighthouse + k6)

**Status**: Aceito — 2025-10-19  
**Atualização**: 2025-11-08 — PRs agora são fail‑closed para Performance e Segurança; o workflow temporário “Quick Perf+Security Check” foi removido. Esta ADR permanece como registro histórico; ver PRs #50, #51 e #52 para a política vigente.
**Owners**: Frontend Foundation Guild (tech), SRE (co-owner)  
**Referências**: Constituição v5.2.0 (Art. IX, Art. XIII), Clarification “Perf-Front” 2025-10-12, BLUEPRINT_ARQUITETURAL.md §4

## Contexto

Os critérios SC-001 (lead time), SC-002 (cobertura visual) e SC-004 (acessibilidade/performance) exigem monitoramento contínuo. A clarificação de 12/10 determinou que:

- **Lighthouse/Playwright-Lighthouse** deve cobrir os indicadores UX (LCP, TTI, CLS) com budgets fail-closed.
- **k6** permanece como guarda-chuva para throughput/latência de APIs expostas ao frontend, validando cabeçalhos multi-tenant (`X-Tenant-Id`, `traceparent`, baggage).
- Pipelines precisam gerar evidências versionadas em runbooks/dashboards e alinhar FinOps (controle de execução de ferramentas de QA).

Sem uma decisão formal havia risco de divergência entre squads, violações da Constituição (Art. IX) e perda de rastreabilidade em incidentes de UX.

## Decisão

1. **Budgets Lighthouse (UX)**  
   - `frontend/lighthouse.config.mjs` mantém LCP ≤ 2.5s p95, TTI ≤ 3.0s p95, CLS ≤ 0.1.  
   - Rodamos via job `performance` no workflow `.github/workflows/ci/frontend-foundation.yml`. Falhas (política vigente em 2025‑11‑08):
     - `pull_request`, `main`, `release/*` e tags: fail-closed (pipeline interrompe).  
     - `workflow_dispatch`: execução de sanidade, pode pular ou relaxar gates conforme configuração.

2. **k6 Smoke e Métricas**  
   - `tests/performance/frontend-smoke.js` orquestra cenários críticos com baggage multi-tenant.  
   - Exporta métricas `foundation_api_throughput` (OTEL) e alimenta dashboards `observabilidade/dashboards/frontend-foundation.json`.

3. **Integração com CI Outage Policy**  
   - O job `ci-outage-guard` executa após `performance` e aplica política fail-open apenas em branches não-release (via `scripts/ci/handle-outage.ts`), registrando o evento `foundation_ci_outage`.

4. **Governança e Evidências**  
   - Painéis adicionam widgets de FinOps/performance.  
   - Runbook documenta ações em caso de budget ≥ 80% e incidentes.  
   - Qualquer alteração de budget deve ser avaliada por Frontend Guild + SRE e atualizada aqui.

## Consequências

- **Repositório** contém:
  - Configurações de Lighthouse, k6 e runbooks atualizados.
  - Scripts de FinOps (`scripts/finops/foundation-costs.ts`) para correlacionar custos das execuções (Chromatic/Lighthouse/pipelines).
  - Painéis Grafana com FinOps, SC-001..SC-005 e error budget.
- **Pipelines**:  
  - Jobs `performance` e `ci-outage-guard` garantem enforcement automático.  
  - Alertas de orçamento ≥ 80% geram follow-up obrigado em FinOps chapter.
- **Riscos Mitigados**:  
  - Evita regressões de UX em tenants críticos.  
  - Mantém rastreabilidade de custos das ferramentas de QA (apoio a NFR-005).  
  - Nota (2025‑11‑08): fail-open controlado deixou de se aplicar a `pull_request`.

## Alternativas Consideradas

| Alternativa | Motivo da Rejeição |
|-------------|--------------------|
| Somente Lighthouse | Não exercita throughput de APIs e não detecta regressões de headers multi-tenant. |
| Apenas k6 | Não cobre métricas de UX renderizadas (LCP/TTI/CLS) exigidas pelo blueprint e SC-004. |
| Perf tooling ad-hoc | Aumenta custo de manutenção e não possui integrações nativas com GitHub Actions/Chromatic. |

## Ações Futuras

- Revisitar budgets trimestralmente com FinOps (considerando novos tenants).  
- Automatizar baselines de `foundation_api_throughput` no mesmo painel FinOps.  
- Integrar testes de performance a slots canário quando o tráfego real estiver disponível.
