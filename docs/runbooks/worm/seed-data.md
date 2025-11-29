# Runbook: Relatórios WORM do seed_data

Escopo: geração e verificação de evidências WORM para execuções `seed_data` (baseline/carga/DR), incluindo checklist automatizado de PII/RLS/contratos/idempotência/rate-limit/SLO.

## Pré-requisitos
- Variáveis exigidas: `SEEDS_WORM_BUCKET`, `SEEDS_WORM_ROLE_ARN`, `SEEDS_WORM_KMS_KEY_ID`, `SEEDS_WORM_RETENTION_DAYS>=365` (fail-close abaixo disso) e `SEED_ENFORCE_WORM_ON_DRY_RUN=true` somente quando quiser forçar WORM em dry-run/CI.
- Manifesto precisa declarar `integrity.manifest_hash`; modos carga/DR exigem evidência WORM antes da promoção (BudgetService).
- Checklist obrigatório em `observabilidade/checklists/seed-worm-checklist.json`; qualquer item reprovado marca o relatório como `failed` e retorna Problem Details `worm_checklist_failed`.

## Fluxo operacional (backend/apps/tenancy/services/seed_worm.py)
1) Construir relatório com `SeedWormService._build_report`: inclui `seed_run_id`, tenant/ambiente/mode, `manifest_hash`, `rate_limit_usage`, `cost_model_version` e resultado do checklist.  
2) Calcular hash canônico (SHA-256) e assinar (`WormSigner`, default `LocalWormSigner`); falha de assinatura → Problem Details `worm_integrity_failed`.  
3) Upload para storage WORM via `WormStorage.upload` (default in-memory, produção usa Object Lock/KMS); metadata inclui tenant/ambiente/seed_run.  
4) Recarregar o payload e verificar hash+assinatura; se divergir, `EvidenceWORM.integrity_status=invalid` e execução é bloqueada (503).  
5) Persistir `EvidenceWORM` com `worm_retention_days`, `signature_hash/algo/key_id/version`, custos estimados/atuais e `integrity_verified_at`. Para checklist reprovado, retorna Problem Details mesmo com evidência gravada.

## Operação e respostas
- Dry-run: pulado por padrão (relatório `status=skipped` sem gravação). Habilite `SEED_ENFORCE_WORM_ON_DRY_RUN=true` para testar o fluxo completo.  
- Sucesso: `ProblemDetail=None`, `integrity_status=verified`, checklist sem falhas.  
- Falhas comuns:  
  - Retenção < 365 dias → `worm_retention_too_low` (503).  
  - Assinatura/hash divergente → `worm_integrity_failed` (503) com status `invalid`.  
  - Checklist com itens falsos → `worm_checklist_failed` (403) e `status=failed` no relatório.

## Governança e CI
- A checklist canônica é validada em CI (workflow `ci-contracts.yml` via `scripts/ci/validate-seed-contracts.sh`); o arquivo deve ser JSON válido com os IDs obrigatórios (`pii_masked`, `rls_enforced`, `contracts_aligned`, `idempotency_reused`, `rate_limit_respected`, `slo_met`).  
- Evidências devem permanecer WORM (retenção mínima 365 dias, modo COMPLIANCE) e referenciar o commit/manifesto usado para a execução.  
- Em incidentes, referencie este runbook e registre o link do relatório WORM na resposta a incidentes.
