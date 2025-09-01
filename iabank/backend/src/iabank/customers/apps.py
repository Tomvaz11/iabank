"""
Configuração do Django App Customers.

Define as configurações específicas do app de clientes,
incluindo inicializações e configurações de signals.
"""

from django.apps import AppConfig


class CustomersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iabank.customers'
    verbose_name = 'Customers'