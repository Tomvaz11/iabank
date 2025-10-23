from django.apps import AppConfig


class ContractsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.contracts'
    verbose_name = 'Contracts Governance'

    def ready(self) -> None:
        from . import signals  # noqa: F401

