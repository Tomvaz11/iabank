# Runbook: Proteção de Dados Sensíveis e Gestão de Segredos

Este runbook operacionaliza o **ADR-010** e garante conformidade com o Artigo XII da Constituição (v5.2.0).

## Objetivo
Assegurar que PII esteja criptografada em nível de campo e que todos os segredos sejam servidos por Vault/KMS com rotação automática.

## Procedimentos de Verificação
1. **Criptografia de campo (pgcrypto)**
   - Verifique migrations recentes para uso de funções `pgcrypto` (`pgp_sym_encrypt`, `pgp_pub_encrypt`).
   - Garanta que colunas PII estejam marcadas com `EncryptedField` (backend) ou equivalente.
   - Rode o script `scripts/security/check_pgcrypto.sh` para validar metadados e confirmar a presença das funções de criptografia.
2. **Mascaramento de PII em logs/traces**
   - Execute `pytest tests/security/test_log_redaction.py` garantindo ausência de PII em logs estruturados.
   - Confirme no collector OpenTelemetry que o processor de atributos `pii_redactor` está habilitado.
3. **Gestão de segredos via Vault/KMS**
   - Verifique pipeline de CI `ci-vault-rotate.yml` para status verde e acompanhe avisos sobre a CLI do Vault.
   - Audite políticas do Vault para cada ambiente (`vault policy read <env>`).
   - Confirme que aplicações usam credenciais efêmeras (`vault auth list`).
4. **Preflight de seed_data (Vault/WORM fail-close)**
   - Confirme variáveis obrigatórias antes de qualquer execução: `VAULT_TRANSIT_PATH`, `SEEDS_WORM_BUCKET`, `SEEDS_WORM_ROLE_ARN`, `SEEDS_WORM_KMS_KEY_ID`, `SEEDS_WORM_RETENTION_DAYS>=365`.
   - RBAC/ABAC: apenas `seed-runner` e `seed-admin` podem prosseguir; ambientes permitidos: dev/homolog/staging/perf. Fora disso, bloqueie com Problem Details `seed_preflight_forbidden`.
   - Dry-run: pode pular WORM apenas quando `SEED_ENFORCE_WORM_ON_DRY_RUN=false`; demais modos exigem WORM ativo (falha 503).
   - Auditoria sem PII: fingerprint de manifesto/paths ao invés de valores literais. Exemplo de checagem local:
     ```bash
     python - <<'PY'
     from backend.apps.tenancy.services.seed_preflight import PreflightContext, SeedPreflightService
     ctx = PreflightContext(
         tenant_id="tenant-a",
         environment="staging",
         manifest_path="configs/seed_profiles/staging/tenant-a.yaml",
         requested_by="svc:seed-runner",
         roles=["seed-runner"],
         dry_run=False,
     )
     result = SeedPreflightService().check(ctx)
     if not result.allowed:
         raise SystemExit(result.problem.as_dict())
     print("Preflight OK", result.audit)
     PY
     ```

## Notas para CI (Vault Rotation Checks)
- Instalação da CLI do Vault no CI: usamos download oficial via `curl` + `unzip` (sem `hashicorp/setup-vault@v2`).
- Teste de redaction de logs: o job cria um `pytest-min.ini` e roda `pytest -c pytest-min.ini -q tests/security/test_log_redaction.py` para evitar herdar `addopts` de cobertura do repositório (e dependências de plugins de cobertura).
- Qualquer alerta/erro sobre cobertura global no job de rotação deve ser ignorado — o teste de redaction é isolado e rápido (apenas valida mascaramento de PII nos logs).

## Resposta a Incidentes
- Em caso de vazamento de PII ou falha de rotação:
  1. Acione o time de segurança (#incident-response).
  2. Revogue tokens comprometidos (`vault token revoke`).
  3. Registre incidente em `docs/runbooks/incident-report.md`.

## Evidências
- Anexe logs dos scripts e snapshots dos dashboards de mascaramento.
- Armazene relatórios no bucket WORM conforme Artigo XVI, assinando o payload (hash SHA-256 + assinatura assimétrica via KMS/Vault, ex.: RSA-PSS-SHA256 ou Ed25519) e verificando a assinatura após o upload.
