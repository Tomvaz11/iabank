"""
Configuração do Django App Users.

Define as configurações específicas do app de usuários,
incluindo inicializações e configurações de signals.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iabank.users'
    verbose_name = 'Users'