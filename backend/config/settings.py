from __future__ import annotations

import json
import os
from pathlib import Path

import structlog

from backend.config.logging_utils import structlog_pii_sanitizer
from backend.config.sentry import init_sentry

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
                structlog_pii_sanitizer,
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
        structlog_pii_sanitizer,
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


def _parse_csp_exceptions(value: str | None) -> list[dict[str, str]]:
    if not value:
        return []

    try:
        raw = json.loads(value)
    except json.JSONDecodeError:
        return []

    if not isinstance(raw, list):
        return []

    normalized: list[dict[str, str]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        directive = str(entry.get('directive', '')).strip()
        exception_value = str(entry.get('value', '')).strip()
        expires_at = str(entry.get('expires_at', '')).strip()
        if not directive or not exception_value or not expires_at:
            continue

        normalized_entry: dict[str, str] = {
            'directive': directive,
            'value': exception_value,
            'expires_at': expires_at,
        }

        note = entry.get('note')
        if isinstance(note, str) and note.strip():
            normalized_entry['note'] = note.strip()

        normalized.append(normalized_entry)

    return normalized


FOUNDATION_CSP = {
    'mode': os.environ.get('FOUNDATION_CSP_MODE', 'auto'),
    'nonce': os.environ.get('FOUNDATION_CSP_NONCE', 'nonce-dev-fallback'),
    'trusted_types_policy': os.environ.get('FOUNDATION_TRUSTED_TYPES_POLICY', 'foundation-ui'),
    'report_uri': os.environ.get('FOUNDATION_CSP_REPORT_URI', 'https://csp-report.iabank.com'),
    'report_only_started_at': os.environ.get('FOUNDATION_CSP_REPORT_ONLY_STARTED_AT'),
    'report_only_ttl_days': os.environ.get('FOUNDATION_CSP_REPORT_ONLY_TTL_DAYS', '30'),
    'connect_src': _parse_csp_list(
        os.environ.get('FOUNDATION_CSP_CONNECT_SRC'),
        ["'self'", 'https://api.iabank.com', 'https://staging-api.iabank.com'],
    ),
    'style_src': _parse_csp_list(os.environ.get('FOUNDATION_CSP_STYLE_SRC'), ["'self'"]),
    'img_src': _parse_csp_list(os.environ.get('FOUNDATION_CSP_IMG_SRC'), ["'self'", 'data:']),
    'font_src': _parse_csp_list(os.environ.get('FOUNDATION_CSP_FONT_SRC'), ["'self'"]),
    'exceptions': _parse_csp_exceptions(os.environ.get('FOUNDATION_CSP_EXCEPTIONS')),
}

SENTRY_ENABLED = init_sentry()
