# Terraform — seed_data (Vault/WORM/filas)

Provisiona dependências de infraestrutura da automação de seeds/factories com fail-close para PII/rollback e off-peak.

## Recursos
- **WORM**: bucket S3 com Object Lock (COMPLIANCE), retenção mínima configurável (default 1855 dias — 30 dias + 5 anos), versioning, SSE-KMS dedicado e bloqueio de acesso público.
- **Fila curta (Redis)**: replication group com failover automático, criptografia em repouso/trânsito, snapshots para rollback e janela de manutenção alinhável ao off-peak.
- **Vault Transit**: mount dedicado + chave FPE determinística por ambiente/tenant e política com privilégio mínimo.

Tags padrão incluem `service=seed-data`, `environment`, `tenant`, `off_peak_window_utc` e `data_classification=internal`.

## Como usar
```bash
cd infra/terraform/seed-data
terraform init -backend=false
terraform validate
# Plano com variáveis de ambiente
TF_VAR_environment=staging \
TF_VAR_tenant_slug=tenant-a \
TF_VAR_redis_auth_token="vault://path/to/token" \
terraform plan -out=plan.out
```

Mantenha `off_peak_window_utc` sincronizado com os manifestos e com a janela do Argo (T084). Ajuste `redis_maintenance_window` para a mesma janela/dia.

## Políticas OPA
As regras em `infra/opa/seed-data/` validam:
- Object Lock + retenção >=1855 dias, versionamento e SSE-KMS no bucket WORM;
- Tags obrigatórias (`service/environment/tenant/off_peak_window_utc`);
- Transit não exportável/sem delete e com convergent encryption;
- Redis com criptografia, failover e snapshots para rollback.

Rode `scripts/ci/validate-opa.sh` para aplicar `terraform fmt/validate` e `opa test` (usa fixture `infra/opa/seed-data/fixtures/plan.json`).
