# Relatório de Execução de Testes — IABANK (F‑10)

Data: 2025-11-04

Este documento consolida a execução dos testes e validações do repositório, incluindo frontend, backend, contratos, performance, linters e formatação. Não há commits; apenas artefatos de saída foram gerados/atualizados localmente.

## Ambiente de Execução
- Node.js: v20.17.0; pnpm: 9.12.2
- Python: 3.12.3 (Poetry 2.2.1; venv local `.venv`)
- Docker Compose: v2.40.3; k6: v1.3.0
- Postgres 15 e Redis 7 provisionados via `infra/docker-compose.foundation.yml` (portas locais 55432/56379 usadas nos testes do backend)

## Resultado Geral
- Status geral: aprovado com observações.
- Frontend: testes unitários, E2E, Lighthouse e Storybook (a11y) aprovados.
- Backend: pytest aprovado com cobertura ≥ 85% (total 87.36%).
- Contratos/API: Spectral OK; openapi-diff sem quebras; Pact OK.
- Performance: k6 smoke executado; thresholds de throughput sinalizaram “critical” (ver observações).
- Linters: ESLint e Ruff sem findings; Prettier apontou 2 arquivos a formatar.

## Frontend
- ESLint: sem erros/avisos.
- TypeScript (tsc --noEmit): sem erros.
- Vitest (unit tests): 26 arquivos, 75 testes — todos aprovados.
- Playwright (E2E): 3/3 aprovados (chromium, firefox, webkit).
- Lighthouse (budgets críticos): aprovado.
- Storybook test-runner (a11y): 4 suítes, 9 testes — aprovados, sem violações axe.
- Prettier (check): pendências em dois arquivos:
  - `frontend/scripts/tokens/index.ts`
  - `frontend/src/shared/config/flags.remote.test.ts`
- PNPM audit (prod, nível ≥ high): 0 vulnerabilidades high/critical.

### Cobertura Visual (Chromatic — checagem local)
- Verificação local com `frontend/scripts/chromatic/check-coverage.ts` (mínimo 95% por tenant): reprovado com o `stories.json` atual.
  - tenant-alfa: 75.00% (faltando: Shared/UI/Button)
  - tenant-beta: 0.00%
  - tenant-default: 0.00%
- Observação: no CI, o job do Chromatic pode estar configurado com `--exit-zero-on-changes`. Se cobertura mínima for gate formal, será necessário complementar stories por tenant.

## Backend
- Ruff: sem findings.
- Bandit (-ll): sem High/Critical.
- Radon (complexidade > 10):
  - `backend/apps/tenancy/models/tenant_theme_token.py:44` — `TenantThemeToken.clean` — C (17)
  - `backend/apps/foundation/api/views.py:175` — `RegisterFeatureScaffoldView` — C (11)
  - `backend/apps/foundation/serializers/theme.py:21` — `_validate_categories` — C (12)
  - `backend/apps/foundation/serializers/theme.py:51` — `TenantThemeSerializer` — C (12)
  - `backend/apps/foundation/serializers/theme.py:58` — `TenantThemeSerializer.to_representation` — C (11)
- Pytest (+ cobertura): 79 aprovados; cobertura total 87.36% (gate ≥ 85%)
  - Pontos com cobertura baixa (não bloqueante pois total ≥ 85%):
    - `backend/apps/foundation/metrics.py` (~62%)
    - `backend/apps/tenancy/views.py` (~78%)
    - `backend/apps/foundation/services/flag_gate.py` (~69%)
    - `backend/apps/contracts/signals.py` (~73%)
    - `backend/config/settings.py` (~66%)
    - (migrations/comandos administrativos têm cobertura menor por natureza)

## Contratos e API
- Spectral (OpenAPI lint): sem erros.
- openapi-diff: sem mudanças breaking; apenas adições non‑breaking.
- openapi-typescript-codegen (generate): executado com sucesso (output em `frontend/src/shared/api/generated`).
- Pact (verify): aprovado (consumer tests para cache/temas/metrics).

## Performance
- k6 smoke (local, 1 VU por 30s) executado com sucesso; checks de status e propagação de trace OK.
- Resultado classificado como "critical" para throughput conforme thresholds definidos no próprio teste (não implica falha de funcionalidade):
  - Artefato JSON: `artifacts/k6-smoke.json`
- Aviso no console: endpoint OTEL ausente para publicação de métricas (informativo no modo local).

## Artefatos/saídas atualizados nesta execução (sem commits)
- `artifacts/k6-smoke.json` — resumo do k6 smoke.
- `observabilidade/data/lighthouse-latest.json` — atualizado pelo teste de Lighthouse.
- `.coverage` — arquivo de cobertura do pytest.

## Próximos Passos sugeridos (opcional)
- Executar Prettier write nos 2 arquivos apontados.
- Decidir sobre o gate de cobertura visual (Chromatic) e, se necessário, adicionar stories por tenant até ≥ 95%.
- Avaliar thresholds/metas do k6 smoke e configurar `OTEL_EXPORTER_OTLP_ENDPOINT` para registrar métricas de throughput quando pertinente.
- (Opcional) Reduzir complexidade das funções sinalizadas pelo radon.
- (Opcional) Aumentar cobertura nos módulos com porcentagens mais baixas.

## Observações de Reprodutibilidade
- Backend testou contra Postgres/Redis do `infra/docker-compose.foundation.yml` publicados em portas não padrão (55432/56379) e variáveis `FOUNDATION_DB_*` setadas na execução do pytest.
- Nenhuma alteração de código foi feita; apenas execução de comandos e geração de artefatos locais.

