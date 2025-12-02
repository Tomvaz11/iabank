# Issue 003 — Endurecer seed_data para fail-close (manifesto, off-peak, CI)

## Contexto e motivação

- Na verificação do spec `specs/003-seed-data-automation/spec.md` vs blueprint, achamos implementações que seguem decisões mais fracas (blueprint) já presentes no código:
  1) **Manifesto opcional e hash vazio**: `seed_data` gera manifesto default quando o arquivo não existe e só bloqueia schema se veio de arquivo. `reference_datetime` cai em fallback `timezone.now()` e `integrity.manifest_hash` pode ficar vazio (`setdefault`). Isso permite execuções sem manifesto versionado/validado. (refs: `backend/apps/tenancy/management/commands/seed_data.py:190-240`, `seed_runs.py:392-395`).
  2) **Janela off-peak com override**: flag `allow_offpeak_override` desativa o bloqueio da janela declarada no manifesto. (ref: `backend/apps/tenancy/services/seed_runs.py:407-430`).
  3) **Dry-run CI fail-open**: `scripts/ci/seed-data-dry-run.sh` retorna sucesso mesmo sem Vault/WORM ou quando o comando não existe, apenas logando o “stub seguro”. (ref: `scripts/ci/seed-data-dry-run.sh:42-60`).
  4) **Pré-condição HTTP branda**: `POST /api/v1/seed-runs/{id}/cancel` responde `412 Precondition Failed` quando falta `If-Match`; o plano exige `428 Precondition Required` para ausência de condicional, mantendo governança de concorrência/idempotência. (ref: `backend/apps/tenancy/views.py` em `SeedRunCancelView`).
- O spec exige fail-close: manifesto v1 obrigatório, hash sha256 obrigatório, `reference_datetime` obrigatório, execução fora da janela deve falhar e CI/PR deve rodar dry-run determinístico de baseline com dependências ativas (FR-004, FR-006, FR-010, FR-012, Edge cases/Q5/Q10).
- Por que mudar:
  - **Reprodutibilidade/auditoria**: impede drift silencioso e assegura trilha WORM/FinOps coerente.
  - **Segurança/PII multi-tenant**: evita execuções com manifesto incompleto ou horário crítico.
  - **Confiança em CI**: captura faltas de dependência cedo; evita “green” falso antes de staging/perf.

## Escopo

1) **Manifesto obrigatório e hash estrito**
   - Remover manifesto default; falhar se `manifest_path` não existir ou não validar no schema v1.
   - Exigir `integrity.manifest_hash` presente e coerente; sem hash → 422.
   - Exigir `reference_datetime` (ISO 8601 UTC); sem fallback para `now`.
2) **Off-peak sem escape**
   - Remover `allow_offpeak_override` ou limitar apenas a modos de manutenção internos; default deve falhar fora da janela declarada.
3) **Dry-run CI bloqueador**
   - Em `scripts/ci/seed-data-dry-run.sh`, se faltar Vault/WORM ou o comando `seed_data`, retornar erro (exit 1) em vez de “stub seguro”.
   - Garantir que o dry-run exercita caminho real quando disponível (fail-close em OTEL/Sentry já simulado com exit 4).
4) **Pré-condição HTTP (`If-Match`)**
   - Alinhar a resposta para ausência de `If-Match` em mutações (ex.: cancel) para `428 Precondition Required` conforme governança de pré-condições; manter `412` apenas quando o valor não coincidir (mismatch).

## Checklist de entrega

- [ ] `seed_data` falha se o manifesto estiver ausente, inválido ou sem hash/reference_datetime; sem manifesto default.
- [ ] Off-peak: remoção ou hardening do override; execuções fora da janela retornam erro conforme spec.
- [ ] Script de CI retorna não-zero na ausência de Vault/WORM ou do comando; dry-run real quando possível.
- [ ] API/mutações retornam `428 Precondition Required` quando falta `If-Match`; `412` apenas para mismatch; testes cobrindo.
- [ ] Testes atualizados cobrindo cenários de ausência de manifesto, hash vazio, referência ausente e janela off-peak.
- [ ] Notas de PR/commit citam que eram divergências de blueprint (mais fraco) e foram alinhadas ao spec 003.

## Validação e testes

- Backend: `cd src && pytest backend/apps/tenancy/tests backend/apps/foundation/tests && ruff check .`
- Casos manuais/automatizados:
  - Manifesto ausente → 422/exit de CLI não-zero.
  - Manifesto sem `integrity.manifest_hash` ou com hash divergente → 422.
  - Manifesto sem `reference_datetime` → erro.
  - Execução fora da janela off-peak → erro (sem override).
  - `scripts/ci/seed-data-dry-run.sh` falha se faltarem VARs de Vault/WORM ou o comando não existir; roda caminho real quando disponível.

## Referências

- Spec: `specs/003-seed-data-automation/spec.md` (FR-004, FR-006, FR-010, FR-012, Edge cases/Q5/Q10).
- Implementação: `backend/apps/tenancy/management/commands/seed_data.py`, `backend/apps/tenancy/services/seed_runs.py`, `scripts/ci/seed-data-dry-run.sh`.
- Blueprint: `BLUEPRINT_ARQUITETURAL.md` (comportamento permissivo de seed_data).
- Adições: `adicoes_blueprint.md` (fail-close, SLO/error budget, observabilidade e controles de segurança que reforçam o endurecimento). 
