# Issue 001 — Alinhar erros, retenção WORM e SLOs ao spec

## Contexto e motivação

- Durante a validação de divergências entre spec (`specs/001-indice-features-template/spec.md`) e blueprint (`BLUEPRINT_ARQUITETURAL.md` + `adicoes_blueprint.md`), encontramos pontos implementados seguindo o blueprint (decisão mais fraca) em vez do spec.
- Itens impactados:
  - **Formato de erros**: endpoints ainda respondem com `{ "errors": ... }` (padrão do blueprint §18) em `backend/apps/foundation/api/views.py`, enquanto o spec exige Problem Details (RFC 9457) com RateLimit-*/Idempotency/ETag/If-Match/428 padronizados.
  - **Retenção WORM**: serviços de seed/WORM (`backend/apps/tenancy/services/seed_worm.py` e `seed_preflight.py`) usam retenção mínima de 365 dias; o spec define 30 dias legais + 5 anos adicionais para trilhas de auditoria LGPD.
  - **SLOs / error budgets / GameDays**: catálogo de SLO (`docs/slo/catalogo-slo.md`) e thresholds de k6 (`tests/performance/frontend-smoke.js`) usam SLI do blueprint (p95 ≤ 500 ms para GET /loans/front, sem p99/MTTR/budget/GameDay). O spec fixa baseline p95 600 ms, p99 1 s, MTTR 1 h, erro <1% + budgets e GameDays bimestrais (500 ms pode ser “stretch”, mas precisa de budget/ritual).
- Por que mudar:
  - **Problem Details**: melhora interoperabilidade, facilita clientes/observabilidade, clarifica precondições (ETag/If-Match/428) e rate limiting/idempotência.
  - **Retenção WORM 30d + 5a**: dá conforto regulatório/auditável (LGPD + prescrições civis/tributárias); 1 ano é curto para SaaS financeiro.
  - **SLO+budget+GameDay**: garante governança de confiabilidade; o alvo p95 600/p99 1000 ms é realista para operação inicial e permite budget; 500 ms pode ficar como stretch por endpoint.

## Escopo

1) **Problem Details (RFC 9457)**
   - Arquivo-alvo: `backend/apps/foundation/api/views.py`
   - Trocar respostas `{ "errors": ... }` por Problem Details com `type`, `title`, `status`, `detail`, `instance`.
   - Garantir headers já usados: `RateLimit-Limit/Remaining/Reset`, `Retry-After`, `Idempotency-Key`, `ETag`, `Location`, `If-Match/If-None-Match` → manter, mas alinhar payload de erro.
   - Atualizar testes correspondentes.

2) **Retenção WORM (30 dias legais + 5 anos adicionais)**
   - Arquivos-alvo: `backend/apps/tenancy/services/seed_worm.py`, `backend/apps/tenancy/services/seed_preflight.py`.
   - Ajustar `min_retention_days` para 30 + (5 * 365) = 184? (usar 30 + 5 anos em dias; se quiser precisão, considerar anos bissextos? padrão: 30 + 1825 = 1855 dias).
   - Atualizar mensagens de validação, testes e qualquer config/default relacionada.

3) **SLOs, budgets e GameDays (baseline p95 600 ms / p99 1 s / MTTR 1 h / erro <1%)**
   - Arquivos-alvo: `docs/slo/catalogo-slo.md`, `tests/performance/frontend-smoke.js`, e qualquer alerta/threshold dependente.
   - Ajustar tabela para refletir os SLOs decididos no spec; manter 500 ms como “stretch” opcional por endpoint se quiser.
   - Garantir menção a error budgets e GameDays (cadência bimestral) alinhados ao spec.

## Checklist de entrega

- [ ] Problem Details implementados em `backend/apps/foundation/api/views.py` (todos os endpoints que ainda retornam `{errors: ...}`).
- [ ] Retenção mínima WORM ajustada para 30d + 5a nos serviços de seed (`seed_worm.py` e `seed_preflight.py`), com testes verdes.
- [ ] Catálogo de SLO e thresholds de k6 atualizados para p95 600 ms / p99 1 s / MTTR 1 h / erro <1%, com budgets e GameDays documentados.
- [ ] Notas de commit/PR (se houver) mencionam que era uma divergência entre blueprint e spec e foi alinhado.

## Validação e testes (ponta a ponta)

- Problem Details: exercitar endpoints tocados (scaffold, tenant-theme, tenant-metrics) e verificar payload RFC 9457 (`type`, `title`, `status`, `detail`, `instance`) e headers (`RateLimit-Limit/Remaining/Reset`, `Retry-After`, `Idempotency-Key`, `ETag/If-Match/If-None-Match`, `Location` quando aplicável). Cobrir cenários 400/404/409/412/428/429.
- Testes automatizados: `cd src && pytest backend/apps/foundation/tests backend/apps/tenancy/tests/test_seed_worm.py backend/apps/tenancy/tests/test_seed_preflight.py` e `ruff check .`.
- WORM: simular emissão com retenção abaixo e acima do mínimo para validar bloqueio e sucesso (mensagens atualizadas para 30d+5a).
- SLOs/thresholds: revisar `docs/slo/catalogo-slo.md` e rodar k6 relevante (ex.: `pnpm k6 run tests/performance/frontend-smoke.js`), conferindo thresholds p95 600 ms / p99 1 s / erro <1%; manter 500 ms como stretch se configurado.
- Registros/artefatos: confirmar que resultados de k6 e SLOs alimentam artefatos/alertas esperados (quando houver pipeline local) e que budgets/GameDays estão documentados.
- Sanidade: smoke rápido de API/health para garantir que ajustes de erro não quebraram rotas de sucesso.

## Referências

- Spec: `specs/001-indice-features-template/spec.md` (metas SLO, Problem Details, retenção WORM 30d + 5a).
- Blueprint: `BLUEPRINT_ARQUITETURAL.md` (padrão `{errors: ...}`, SLI 500 ms, sem budgets/GameDay).
- Adições: `adicoes_blueprint.md` (SLO/error budget, WORM, RateLimit/Idempotency/ETag).

## Notas rápidas de teste/validação

- Rodar `cd src && pytest && ruff check .` (conforme comando padrão no AGENTS).
- Executar testes específicos tocados (ex.: `pytest backend/apps/foundation/tests` e `backend/apps/tenancy/tests/test_seed_worm.py`, `test_seed_preflight.py`).
- Se mexer em SLO/thresholds, rodar `pnpm k6`/`pnpm test` conforme scripts existentes para garantir que os thresholds estão coerentes.
