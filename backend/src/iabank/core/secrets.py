import os
from typing import Optional
from django.conf import settings


class SecretsManager:
    """Centraliza gestão de secrets para produção."""

    @staticmethod
    def get_secret(key: str, default: Optional[str] = None) -> str:
        """Busca secret de AWS Secrets Manager ou variável ambiente."""
        if settings.DEBUG:
            # Development: usar .env
            return os.getenv(key, default)
        else:
            # Production: AWS Secrets Manager
            try:
                import boto3
                client = boto3.client('secretsmanager')
                response = client.get_secret_value(SecretId=f"iabank/{key}")
                return response['SecretString']
            except Exception as e:
                # Fallback para env var
                return os.getenv(key, default)