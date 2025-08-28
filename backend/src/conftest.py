import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iabank.settings')

def pytest_configure(config):
    """Configure Django settings for pytest."""
    django.setup()
    settings.DEBUG = False
    settings.DATABASES['default']['NAME'] = ':memory:'