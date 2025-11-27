# Preflight de seed_data (Vault/WORM)

Checklist minimo para liberar execucoes `seed_data` via CLI/API em qualquer ambiente:

- **Vault Transit**: path dedicado por ambiente/tenant (`VAULT_TRANSIT_PATH`) disponivel e com politica `seed-data` de minimo privilegio. Auditoria do Vault deve registrar apenas fingerprints (sem manifestos completos).
- **WORM**: bucket com Object Lock ativo, role (`SEEDS_WORM_ROLE_ARN`) e KMS (`SEEDS_WORM_KMS_KEY_ID`) configurados. Retencao minima `SEEDS_WORM_RETENTION_DAYS >= 365`.
- **RBAC/ABAC**: somente perfis `seed-runner` e `seed-admin` liberados; ambientes permitidos: dev/homolog/staging/perf. Use a matriz de bindings em `configs/rbac/seed-data.yaml` quando disponivel.
- **Dry-run**: pode pular WORM apenas se `SEED_ENFORCE_WORM_ON_DRY_RUN=false`; demais modos falham fail-close quando WORM/Vault estiverem indisponiveis.
- **Observabilidade**: spans/metrics/logs devem incluir `seed_preflight` com labels `tenant_id`, `environment`, `requested_by`; export falho bloqueia execucao.

Ferramenta de apoio: `backend.apps.tenancy.services.seed_preflight.SeedPreflightService` valida os requisitos e retorna Problem Details (403 para RBAC/ambiente, 503 para dependencias).
