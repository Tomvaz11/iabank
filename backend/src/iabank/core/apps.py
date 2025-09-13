from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "iabank.core"
    verbose_name = "Core"

    def ready(self):
        # Import signals if any
        pass
