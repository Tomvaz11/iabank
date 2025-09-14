"""
Configuração global para todos os testes.

Setup do Django e pytest para project IABANK.
"""

import os
import sys
from pathlib import Path
import django
from django.conf import settings
from django.test.utils import get_runner

# Add src to Python path
backend_root = Path(__file__).parent.parent
src_path = backend_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def pytest_configure(config):
    """Configure Django settings for tests."""
    if not settings.configured:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
        django.setup()

    # Register custom markers to avoid warnings
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "contract: Contract tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "tenant_isolation: Tests for tenant isolation")