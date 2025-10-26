from __future__ import annotations

import os
from pathlib import Path

import structlog

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-front-foundation'
DEBUG = True
ALLOWED_HOSTS: list[str] = ['*']

INSTALLED_APPS = [
    'django_prometheus',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'ratelimit',
    'backend.apps.contracts',
    'backend.apps.tenancy',
    'backend.apps.foundation',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'backend.apps.foundation.middleware.security.ContentSecurityPolicyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'backend.config.urls'

TEMPLATES = [
    {
      'BACKEND': 'django.template.backends.django.DjangoTemplates',
      'DIRS': [],
      'APP_DIRS': True,
      'OPTIONS': {
          'context_processors': [
              'django.template.context_processors.debug',
              'django.template.context_processors.request',
              'django.contrib.auth.context_processors.auth',
              'django.contrib.messages.context_processors.messages',
          ],
      },
    },
]

WSGI_APPLICATION = 'backend.config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

PGCRYPTO_KEY = os.environ.get('FOUNDATION_PGCRYPTO_KEY', 'dev-only-pgcrypto-key')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structlog': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.processors.JSONRenderer(),
            'foreign_pre_chain': [
                structlog.processors.TimeStamper(fmt='iso'),
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
            ],
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structlog',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'backend.apps.tenancy': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

DATABASE_ROUTERS = ['backend.config.dbrouter.PostgresOnlyRouter']


def _parse_csp_list(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    items = [item.strip() for item in value.split(',') if item.strip()]
    return items or default


FOUNDATION_CSP = {
    'mode': os.environ.get('FOUNDATION_CSP_MODE', 'report-only'),
    'nonce': os.environ.get('FOUNDATION_CSP_NONCE', 'nonce-dev-fallback'),
    'trusted_types_policy': os.environ.get('FOUNDATION_TRUSTED_TYPES_POLICY', 'foundation-ui'),
    'report_uri': os.environ.get('FOUNDATION_CSP_REPORT_URI', 'https://csp-report.iabank.com'),
    'connect_src': _parse_csp_list(
        os.environ.get('FOUNDATION_CSP_CONNECT_SRC'),
        ["'self'", 'https://api.iabank.com', 'https://staging-api.iabank.com'],
    ),
    'style_src': _parse_csp_list(os.environ.get('FOUNDATION_CSP_STYLE_SRC'), ["'self'"]),
    'img_src': _parse_csp_list(os.environ.get('FOUNDATION_CSP_IMG_SRC'), ["'self'", 'data:']),
    'font_src': _parse_csp_list(os.environ.get('FOUNDATION_CSP_FONT_SRC'), ["'self'"]),
}
