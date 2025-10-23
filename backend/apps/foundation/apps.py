from __future__ import annotations

from django.apps import AppConfig


class FoundationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.foundation'
    verbose_name = 'Frontend Foundation'
