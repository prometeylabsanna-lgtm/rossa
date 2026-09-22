"""Middleware для тестового деплою на Vercel."""
from __future__ import annotations

import fcntl
import os
import shutil
from pathlib import Path

from django.conf import settings


def _ensure_runtime_db() -> None:
    db_name = settings.DATABASES['default']['NAME']
    if not str(db_name).startswith('/tmp/'):
        return
    runtime = Path(db_name)
    if runtime.exists():
        return
    template = Path(settings.BASE_DIR) / 'db.vercel.sqlite3'
    if template.exists():
        shutil.copy2(template, runtime)
        return
    from django.core.management import call_command

    call_command('migrate', '--noinput', verbosity=0)
    call_command('seed_demo', verbosity=0)


def _ensure_ready() -> None:
    marker = Path('/tmp/rossa_ready')
    if marker.exists() and Path(settings.DATABASES['default']['NAME']).exists():
        return

    lock_path = Path('/tmp/rossa_init.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('w') as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        if marker.exists() and Path(settings.DATABASES['default']['NAME']).exists():
            return
        _ensure_runtime_db()
        marker.touch()


class VercelBootstrapMiddleware:
    """Один раз на cold start: SQLite з шаблону збірки → /tmp."""

    def __init__(self, get_response):
        self.get_response = get_response
        if os.environ.get('VERCEL') and not os.environ.get('VERCEL_BUILD'):
            try:
                _ensure_ready()
            except Exception:
                # Не валимо імпорт додатку; помилка зʼявиться в логах запиту.
                import logging

                logging.getLogger(__name__).exception('Vercel bootstrap failed')

    def __call__(self, request):
        if os.environ.get('VERCEL') and not os.environ.get('VERCEL_BUILD'):
            _ensure_ready()
        return self.get_response(request)


class VercelHostMiddleware:
    """Дозволяє поточний *.vercel.app хост у CSRF_TRUSTED_ORIGINS і ALLOWED_HOSTS."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        if host.endswith('.vercel.app'):
            origin = f'https://{host}'
            trusted = list(getattr(settings, 'CSRF_TRUSTED_ORIGINS', []) or [])
            if origin not in trusted:
                trusted.append(origin)
                settings.CSRF_TRUSTED_ORIGINS = trusted
            allowed = list(settings.ALLOWED_HOSTS or [])
            if host not in allowed and '.vercel.app' not in allowed:
                allowed.append(host)
                settings.ALLOWED_HOSTS = allowed
        return self.get_response(request)
