"""
Configuração do Django App Core.

Define as configurações específicas do app core, incluindo
inicializações e configurações de signals se necessário.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iabank.core'
    verbose_name = 'Core'