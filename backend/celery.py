from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


def _import_celery_package():
    """
    Garante que a importação do pacote `celery` use o módulo da dependência,
    evitando o shadowing do arquivo local backend/celery.py quando `sys.path`
    inclui o diretório do projeto no início (pytest-django).
    """
    base_dir = Path(__file__).resolve().parent
    removed = False
    if str(base_dir) in sys.path:
        sys.path.remove(str(base_dir))
        removed = True
    try:
        return importlib.import_module('celery')
    finally:
        if removed:
            sys.path.insert(0, str(base_dir))


Celery = _import_celery_package().Celery

# Garante que as settings do Django sejam carregadas antes de inicializar o app Celery.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')

celery_app = Celery('backend')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()


@celery_app.task(name='seed_data.healthcheck', acks_late=True)
def healthcheck() -> str:
    """
    Task simples usada para validar roteamento/acks-late das filas configuradas.
    """
    return 'ok'


__all__ = ('celery_app',)
