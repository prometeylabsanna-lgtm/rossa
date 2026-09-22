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

CSRF_TRUSTED_ORIGINS = []

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SERVE_MEDIA = True

# Збірка (локально / Vercel build): файли в репо.
# Runtime на Vercel: SQLite у /tmp (записуваний), медіа — з пакета (read-only).
_IS_VERCEL_RUNTIME = bool(os.environ.get('VERCEL')) and not bool(os.environ.get('VERCEL_BUILD'))

_DB_TEMPLATE = BASE_DIR / 'db.vercel.sqlite3'
_MEDIA_PACKAGED = BASE_DIR / 'media_demo'

if _IS_VERCEL_RUNTIME:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/rossa.sqlite3',
        }
    }
    MEDIA_ROOT = _MEDIA_PACKAGED if _MEDIA_PACKAGED.exists() else Path('/tmp/media')
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(_DB_TEMPLATE),
        }
    }
    MEDIA_ROOT = _MEDIA_PACKAGED

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'core.middleware_vercel.VercelHostMiddleware',
    'core.middleware_vercel.VercelBootstrapMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'csp.middleware.CSPMiddleware',
]

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

LOGGING['root']['level'] = 'INFO'  # noqa: F405
CSP_REPORT_ONLY = True
