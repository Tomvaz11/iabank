# 10. Proteção de Dados Sensíveis e Gestão de Segredos

**Status:** Aprovado

**Contexto:** O Artigo XII (Segurança por Design) da Constituição impõe que dados sensíveis sejam protegidos em todas as camadas e que segredos tenham rotação automatizada. As diretrizes internas de segurança corporativa especificam práticas concretas (pgcrypto, mascaramento de PII, Vault, KMS) que excedem o nível estratégico da Constituição, mas precisam ser seguidas para manter o alinhamento enterprise.

**Decisão:**
- **Criptografia de campo:** Campos que armazenam PII (CPF/CNPJ, e-mail, telefone, dados bancários) DEVEM ser criptografados com `pgcrypto` (ou equivalente suportado pelo PostgreSQL) usando chaves gerenciadas externamente.
- **Mascaramento de PII em logs e telemetria:** Logs estruturados, traces e métricas DEVEM remover ou mascarar PII antes do envio. O coletor OpenTelemetry DEVE aplicar processadores de atributos para garantir a remoção desses dados.
- **Gestão de segredos:** Segredos de aplicação DEVEM residir em **HashiCorp Vault** com rotação automática e uso de **envelope encryption** via **KMS** do provedor cloud. Cada ambiente possui sua própria chave e política.
- **Cofre como única fonte:** Aplicações não armazenam segredos em arquivos ou variáveis persistentes; sempre buscam valores no cofre através de credenciais efêmeras.

**Consequências:**
- O pipeline de CI/CD deve executar verificações para assegurar que campos marcados como PII estejam protegidos por criptografia e testes automatizados devem validar o mascaramento em logs.
- Operações que envolvam novos campos sensíveis exigem atualização das políticas do Vault e das chaves no KMS.
- Falhas de rotação ou exposição de PII em logs são tratadas como incidentes de segurança e devem seguir o runbook correspondente.

**Referências Operacionais:**
- Runbook principal: `docs/runbooks/seguranca-pii-vault.md`
- Checklist de CI: `docs/pipelines/ci-required-checks.md`
