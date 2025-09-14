"""
Development settings for IABANK project.
"""

from .base import *

# Debug toolbar and development tools
DEBUG = True

# Additional apps for development
INSTALLED_APPS += [
    # Add development-specific apps here if needed
]

# Development-specific middleware
MIDDLEWARE = [
    # Add development-specific middleware here if needed
] + MIDDLEWARE

# PostgreSQL configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="iabank"),
        "USER": config("DB_USER", default="iabank_user"),
        "PASSWORD": config("DB_PASSWORD", default="iabank_pass"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5433", cast=int),
        "OPTIONS": {
            "client_encoding": "UTF8",
        },
        "TEST": {
            "NAME": "test_iabank_dev",
        },
    }
}

# Note: SQLite is not supported in IABANK due to multi-tenancy requirements
# This project requires PostgreSQL for Row-Level Security (RLS) and PITR features

# Cache - Use Redis even in development (container must be running)
# CACHES setting inherited from base.py

# Celery - Use in-memory broker for development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Disable HTTPS requirements in development
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = None
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Logging - More verbose in development
LOGGING["loggers"]["iabank"]["level"] = "DEBUG"
LOGGING["loggers"]["django"]["level"] = "DEBUG"

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Development-specific settings
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]
