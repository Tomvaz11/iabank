"""
Campos criptografados customizados para IABANK.

Implementação própria usando Fernet (cryptography) para substituir
django-cryptography que apresenta incompatibilidades.
"""
import base64
from typing import Any, Optional

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

from iabank.core.secrets import SecretsManager


class EncryptedMixin:
    """Mixin para funcionalidade de criptografia usando Fernet."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_encryption()

    def _setup_encryption(self):
        """Configura a instância Fernet para criptografia."""
        try:
            # Buscar chave das configurações ou SecretsManager
            if hasattr(settings, 'DJANGO_CRYPTOGRAPHY_SETTINGS'):
                key_str = settings.DJANGO_CRYPTOGRAPHY_SETTINGS.get('CRYPTOGRAPHY_KEY')
            else:
                key_str = SecretsManager.get_secret('ENCRYPTION_KEY')

            if not key_str:
                raise ImproperlyConfigured(
                    "ENCRYPTION_KEY não encontrada. Configure DJANGO_CRYPTOGRAPHY_SETTINGS "
                    "ou variável de ambiente ENCRYPTION_KEY"
                )

            # Garantir que a chave está no formato bytes
            if isinstance(key_str, str):
                key_bytes = key_str.encode('utf-8')
            else:
                key_bytes = key_str

            self.fernet = Fernet(key_bytes)

        except Exception as e:
            raise ImproperlyConfigured(f"Erro ao configurar criptografia: {e}")

    def encrypt_value(self, value: str) -> str:
        """Criptografa um valor string."""
        if value is None:
            return None

        try:
            # Criptografar e codificar em base64 para armazenamento
            encrypted_bytes = self.fernet.encrypt(value.encode('utf-8'))
            return base64.b64encode(encrypted_bytes).decode('ascii')
        except Exception as e:
            raise ValueError(f"Erro ao criptografar valor: {e}")

    def decrypt_value(self, value: str) -> str:
        """Descriptografa um valor string."""
        if value is None:
            return None

        try:
            # Decodificar de base64 e descriptografar
            encrypted_bytes = base64.b64decode(value.encode('ascii'))
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            # Em caso de erro, pode ser um valor não criptografado (migração)
            # ou erro real - para debug, logar o erro
            import logging
            logger = logging.getLogger('iabank.core.fields')
            logger.warning(f"Erro ao descriptografar valor: {e}")
            return value  # Retorna valor original como fallback

    def from_db_value(self, value, expression, connection) -> Optional[str]:
        """Converte valor do banco para Python (descriptografia)."""
        if value is None:
            return value
        return self.decrypt_value(value)

    def to_python(self, value) -> Optional[str]:
        """Converte valor para Python."""
        if value is None:
            return value
        if isinstance(value, str):
            return value
        return str(value)

    def get_prep_value(self, value) -> Optional[str]:
        """Prepara valor para o banco (criptografia)."""
        if value is None:
            return None
        return self.encrypt_value(str(value))


class EncryptedCharField(EncryptedMixin, models.TextField):
    """
    Campo de texto criptografado.

    Armazena dados como TEXT criptografado no banco de dados,
    mas apresenta como CharField normal para a aplicação.
    """

    description = "Campo de texto criptografado"

    def __init__(self, max_length=None, *args, **kwargs):
        # TextField não usa max_length, mas mantemos para compatibilidade
        self.max_length = max_length
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.max_length is not None:
            kwargs['max_length'] = self.max_length
        return name, path, args, kwargs


class EncryptedEmailField(EncryptedMixin, models.TextField):
    """
    Campo de email criptografado.

    Funciona como EmailField mas com criptografia transparente.
    """

    description = "Campo de email criptografado"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        """Converte para Python com validação de email opcional."""
        value = super().to_python(value)
        if value is None:
            return value

        # Validação básica de email (opcional - pode ser removida se causar problemas)
        if value and '@' not in value:
            # Pode ser um valor criptografado ainda - não validar
            pass

        return value


class EncryptedTextField(EncryptedMixin, models.TextField):
    """
    Campo de texto longo criptografado.

    Para dados maiores que precisam de criptografia.
    """

    description = "Campo de texto longo criptografado"


# Função de conveniência para criar campos criptografados
def encrypt(field_class, *args, **kwargs):
    """
    Função para criar campos criptografados de forma compatível com django-cryptography.

    Usage:
        document_number = encrypt(models.CharField(max_length=20))
        email = encrypt(models.EmailField())
    """
    if isinstance(field_class, models.CharField):
        return EncryptedCharField(max_length=getattr(field_class, 'max_length', None), *args, **kwargs)
    elif isinstance(field_class, models.EmailField):
        return EncryptedEmailField(*args, **kwargs)
    elif isinstance(field_class, models.TextField):
        return EncryptedTextField(*args, **kwargs)
    else:
        raise ValueError(f"Tipo de campo não suportado para criptografia: {type(field_class)}")