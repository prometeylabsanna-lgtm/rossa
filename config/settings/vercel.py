"""Тестовий деплой на Vercel (Hobby): без обовʼязкових env-змінних."""
import os
from pathlib import Path

from .base import *  # noqa: F403

DEBUG = False

# Демо-ключ лише для безкоштовного тестового Vercel. Не для продакшену.
SECRET_KEY = 'vercel-demo-only-insecure-key-not-for-production'

ALLOWED_HOSTS = [
    '.vercel.app',
    'localhost',
    '127.0.0.1',
    'testserver',
]

# Wildcard для preview/production *.vercel.app (Django 4.0+).
CSRF_TRUSTED_ORIGINS = ['https://*.vercel.app']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# SQLite у /tmp не шариться між інстансами Vercel — сесії лише в підписаній cookie.
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
# Ліміт Vercel Function body ≈ 4.5 МБ — ріжемо раніше з зрозумілою помилкою Django.
DATA_UPLOAD_MAX_MEMORY_SIZE = 3 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 3 * 1024 * 1024

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SERVE_MEDIA = True

# Збірка (локально / Vercel build): файли в репо.
# Runtime на Vercel: SQLite у /tmp (записуваний), медіа — запис у /tmp, читання з media_demo.
_IS_VERCEL_RUNTIME = bool(os.environ.get('VERCEL')) and not bool(os.environ.get('VERCEL_BUILD'))

_DB_TEMPLATE = BASE_DIR / 'db.vercel.sqlite3'
_MEDIA_PACKAGED = BASE_DIR / 'media_demo'
MEDIA_PACKAGED_ROOT = _MEDIA_PACKAGED

if _IS_VERCEL_RUNTIME:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/rossa.sqlite3',
        }
    }
    MEDIA_ROOT = Path('/tmp/media')
    STORAGES = {
        'default': {
            'BACKEND': 'core.storage_vercel.VercelMediaStorage',
            'OPTIONS': {
                'location': str(MEDIA_ROOT),
                'base_url': MEDIA_URL,
                'packaged_root': str(_MEDIA_PACKAGED),
            },
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
        },
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(_DB_TEMPLATE),
        }
    }
    MEDIA_ROOT = _MEDIA_PACKAGED
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
        },
    }

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'core.middleware_vercel.VercelHostMiddleware',
    'core.middleware_vercel.VercelBootstrapMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'core.middleware_admin.AdminForceUkrainianMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'csp.middleware.CSPMiddleware',
]

LOGGING['root']['level'] = 'INFO'  # noqa: F405

# django-csp 4.x: CSP_REPORT_ONLY застарів — лише CONTENT_SECURITY_POLICY_REPORT_ONLY.
CONTENT_SECURITY_POLICY_REPORT_ONLY = CONTENT_SECURITY_POLICY  # noqa: F405
CONTENT_SECURITY_POLICY = None
