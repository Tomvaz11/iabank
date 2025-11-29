# ROPA/RIPD - seed_data e factories

- **Escopo**: automacao de seeds baseline/carga/DR e factories deterministicas para ambientes dev/homolog/staging/perf; dados 100% sinteticos (sem snapshots).
- **Controlador/Operador**: IABank (time de dados sinteticos). DPO: privacy@iabank.local. Processadores: AWS (WORM/KMS), Vault (Transit).
- **Base legal**: teste de sistemas e validacao de resiliencia/DR (interesse legitimo com minimizacao de dados; consentimento nao aplicavel por ser dado sintetico).
- **Categorias de dados**: identificadores sinteticos de clientes/contas/enderecos/contratos (mascarados via Vault Transit FPE + pgcrypto). Sem dados sensiveis reais.
- **Finalidade**: gerar massa de dados deterministica para testes/DR, validar SLO/FinOps e contratos `/api/v1`, produzir evidencias WORM assinadas.
- **Retencao**: datasets com TTL por modo (baseline/carga/dr); relatorios WORM retidos >=365 dias (`SEEDS_WORM_RETENTION_DAYS`). Checkpoints/datasets limpos antes de reexecucoes de carga/DR.
- **Compartilhamento**: proibida transferencia externa; stubs Pact/Prism bloqueiam chamadas reais. Outbound real falha em fail-close.
- **Seguranca**: RLS obrigatorio; RBAC/ABAC minimo (`seed-runner`, `seed-admin`, `seed-read`); Vault Transit FPE; logs/traces com redacao de PII; WORM com assinatura/verificacao; OTEL/Sentry fail-close; gate automático `scripts/ci/check-audit-cleanliness.sh` reprova logs/WORM sem labels (tenant/environment/seed_run/manifest/mode) ou com PII não redigida.
- **Direitos do titular**: nao aplicavel (dados sinteticos). Caso dados reais sejam inadvertidamente inseridos, fluxo de incident response deve revogar tokens e limpar datasets (ver `docs/runbooks/incident-response.md`).
- **Evidencias**: relatorios WORM assinados armazenam manifesto, hash, volumetria, uso de rate-limit/budget, Problem Details e versao do cost-model (`configs/finops/seed-data.cost-model.yaml`). CI roda `scripts/ci/validate-finops.sh` e `scripts/ci/check-migrations.sh` como gates de compliance.
