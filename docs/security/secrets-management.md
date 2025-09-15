# IABANK Secrets Management

## Development

- Secrets em .env file (não versionado)
- Encryption key local em .env
- Chaves de desenvolvimento padrão para facilitar setup inicial

### Variáveis de Ambiente Necessárias

```bash
# .env (development)
SECRET_KEY=your-django-secret-key
DB_PASSWORD=your-db-password
ENCRYPTION_KEY=your-32-char-encryption-key
ENCRYPTION_SALT=your-encryption-salt
```

## Production

- AWS Secrets Manager para secrets críticos
- IAM roles com least privilege
- Encryption keys rotacionadas automaticamente
- Fallback para variáveis de ambiente se AWS Secrets Manager não disponível

### AWS Secrets Manager Structure

```json
{
  "SecretId": "iabank/SECRET_KEY",
  "SecretString": "production-secret-key"
}
```

## Secrets Structure

- `iabank/SECRET_KEY` - Django secret key
- `iabank/DB_PASSWORD` - Database password
- `iabank/ENCRYPTION_KEY` - Key para criptografia de campos PII
- `iabank/ENCRYPTION_SALT` - Salt para criptografia

## Uso no Código

```python
from iabank.core.secrets import SecretsManager

# Buscar secret com fallback
api_key = SecretsManager.get_secret('API_KEY', 'default-value')

# Em models com campos PII criptografados
from iabank.core.fields import EncryptedCharField, EncryptedEmailField, encrypt

class Customer(BaseTenantModel):
    name = models.CharField(max_length=255)

    # Campos PII automaticamente criptografados
    document_number = EncryptedCharField(max_length=20)
    email = EncryptedEmailField()
    phone = EncryptedCharField(max_length=15)

    # Ou usando função encrypt (compatibilidade)
    credit_card = encrypt(models.CharField(max_length=19))

    # Campos normais
    city = models.CharField(max_length=100)
```

## Implementação Customizada

O IABANK utiliza uma implementação customizada de criptografia baseada no **Fernet** (cryptography library) devido a incompatibilidades com django-cryptography.

### Características:

- **Criptografia**: Fernet (AES 128 com autenticação)
- **Armazenamento**: Base64 em campos TEXT no PostgreSQL
- **Performance**: Criptografia/descriptografia transparente
- **Busca**: Funciona normalmente (Django filtra após descriptografar)
- **Compatibilidade**: API compatível com django-cryptography

## Security Best Practices

1. **Rotation**: Keys devem ser rotacionadas regularmente
2. **Access Control**: Apenas aplicações autorizadas podem acessar secrets
3. **Audit**: Todos os acessos a secrets são logados
4. **Encryption**: Secrets são sempre criptografados em trânsito e repouso
5. **Separation**: Secrets de desenvolvimento e produção completamente separados

## Troubleshooting

### Development Issues

- Verificar se .env existe e contém todas as variáveis necessárias
- Validar formato das chaves de criptografia (32 characters)
- Confirmar que django-cryptography está instalado

### Production Issues

- Verificar IAM roles e policies do AWS Secrets Manager
- Confirmar que região está configurada corretamente
- Verificar fallback para variáveis de ambiente
- Monitorar logs para erros de acesso a secrets

## Migration Guide

Para migrar campos existentes para criptografia:

1. Backup completo do banco
2. Adicionar novos campos criptografados
3. Migrar dados dos campos antigos
4. Remover campos não-criptografados
5. Validar integridade dos dados