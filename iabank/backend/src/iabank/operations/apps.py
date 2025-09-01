"""
Configuração do Django App Operations.

Define as configurações específicas do app de operações,
incluindo inicializações e configurações de signals.
"""

from django.apps import AppConfig


class OperationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iabank.operations'
    verbose_name = 'Operations'