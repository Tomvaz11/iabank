"""
ASGI config for IABANK project.

Expõe a aplicação ASGI como uma variável de módulo chamada ``application``.
Para mais informações sobre este arquivo, consulte:
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iabank.settings')

application = get_asgi_application()