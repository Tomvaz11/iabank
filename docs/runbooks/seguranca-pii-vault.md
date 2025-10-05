# Runbook: Proteção de Dados Sensíveis e Gestão de Segredos

Este runbook operacionaliza o **ADR-010** e garante conformidade com o Artigo XII da Constituição (v5.1.1).

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

## Resposta a Incidentes
- Em caso de vazamento de PII ou falha de rotação:
  1. Acione o time de segurança (#incident-response).
  2. Revogue tokens comprometidos (`vault token revoke`).
  3. Registre incidente em `docs/runbooks/incident-report.md`.

## Evidências
- Anexe logs dos scripts e snapshots dos dashboards de mascaramento.
- Armazene relatórios no bucket WORM conforme Artigo XVI.
