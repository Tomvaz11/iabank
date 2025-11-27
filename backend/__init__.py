default_app_config = 'backend.apps.tenancy.apps.TenancyConfig'
# CI: validação prática da issue #86 (canário) — alteração sem efeito funcional

# Expondo o app Celery para permitir auto-discovery de tasks pelas ferramentas.
from backend.celery import celery_app  # noqa: E402,F401

__all__ = ('celery_app',)
