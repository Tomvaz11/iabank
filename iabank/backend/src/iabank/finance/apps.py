"""
Configuração do Django App Finance.

Define as configurações específicas do app financeiro,
incluindo inicializações e configurações de signals.
"""

from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iabank.finance'
    verbose_name = 'Finance'