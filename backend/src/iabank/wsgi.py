"""
WSGI config for IABANK project.

Expõe a aplicação WSGI como uma variável de módulo chamada ``application``.
Para mais informações sobre este arquivo, consulte:
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iabank.settings')

application = get_wsgi_application()