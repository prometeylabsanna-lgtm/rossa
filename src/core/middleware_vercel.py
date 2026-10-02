"""Middleware для тестового деплою на Vercel."""
from __future__ import annotations

import logging
import os
import shutil
import sqlite3
import time
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

# Піднімай при несумісних змінах схеми — форсує перезбірку /tmp.
SCHEMA_VERSION = '2026-10-02-catalog-0010-leads'

REQUIRED_TABLES = frozenset({
    'auth_user',
    'catalog_category',
    'catalog_product',
    'catalog_characteristic',
    'catalog_productcharacteristic',
    'catalog_productcoloroption',
    'catalog_fabric',
    'leads_orderrequest',
    'leads_partnershiplead',
    'leads_contactlead',
})


def _db_template_path() -> Path:
    return Path(settings.BASE_DIR) / 'db.vercel.sqlite3'


def _template_signature() -> str:
    template = _db_template_path()
    if not template.exists():
        return 'none'
    st = template.stat()
    return f'{int(st.st_mtime)}:{st.st_size}'


def _expected_marker() -> str:
    return f'{SCHEMA_VERSION}|{_template_signature()}'


def _db_is_healthy(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 1024:
        return False
    try:
        con = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
        try:
            tables = {
                row[0]
                for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            return REQUIRED_TABLES.issubset(tables)
        finally:
            con.close()
    except Exception:
        logger.exception('Vercel DB health check failed: %s', path)
        return False


def _close_connections() -> None:
    from django.db import connections

    connections.close_all()


def _migrate() -> None:
    from django.core.management import call_command

    _close_connections()
    call_command('migrate', '--noinput', verbosity=0)
    _close_connections()


def _seed_best_effort() -> None:
    from django.core.management import call_command

    try:
        _close_connections()
        call_command('seed_demo', verbosity=0)
        _close_connections()
    except Exception:
        logger.exception('Vercel seed_demo failed (schema may still be OK)')


def _with_lock(fn) -> None:
    lock_path = Path('/tmp/rossa_init.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    got_lock = False
    for _ in range(100):
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            got_lock = True
            break
        except FileExistsError:
            # Застарілий lock після freeze інстансу.
            try:
                age = time.time() - lock_path.stat().st_mtime
                if age > 60:
                    lock_path.unlink(missing_ok=True)
                    continue
            except OSError:
                pass
            time.sleep(0.1)
    try:
        fn()
    finally:
        if got_lock:
            lock_path.unlink(missing_ok=True)


def _ensure_runtime_db(*, force: bool = False) -> None:
    db_name = settings.DATABASES['default']['NAME']
    if not str(db_name).startswith('/tmp/'):
        return

    runtime = Path(db_name)
    template = _db_template_path()
    healthy = (not force) and _db_is_healthy(runtime)

    if healthy:
        _migrate()
        if _db_is_healthy(runtime):
            return

    _close_connections()
    if runtime.exists():
        try:
            runtime.unlink()
        except OSError:
            logger.exception('Cannot remove stale runtime DB %s', runtime)

    runtime.parent.mkdir(parents=True, exist_ok=True)

    if template.exists() and _db_is_healthy(template):
        shutil.copy2(template, runtime)
        _migrate()
        if _db_is_healthy(runtime):
            return

    # Немає валідного шаблону — зібрати з нуля.
    _migrate()
    _seed_best_effort()
    if not _db_is_healthy(runtime):
        raise RuntimeError('Vercel SQLite is unhealthy after migrate/seed')


def ensure_vercel_db(*, force: bool = False) -> bool:
    """Публічний хук: True якщо runtime DB здорова."""
    if not (os.environ.get('VERCEL') and not os.environ.get('VERCEL_BUILD')):
        return True

    marker = Path('/tmp/rossa_ready')
    runtime = Path(settings.DATABASES['default']['NAME'])
    expected = _expected_marker()

    if (
        not force
        and marker.exists()
        and runtime.exists()
        and marker.read_text().strip() == expected
        and _db_is_healthy(runtime)
    ):
        return True

    def _run() -> None:
        if (
            not force
            and marker.exists()
            and runtime.exists()
            and marker.read_text().strip() == expected
            and _db_is_healthy(runtime)
        ):
            return
        _ensure_runtime_db(force=force)
        marker.write_text(expected)

    _with_lock(_run)
    return _db_is_healthy(Path(settings.DATABASES['default']['NAME']))


class VercelBootstrapMiddleware:
    """Cold start: валідна SQLite у /tmp (шаблон зі збірки або migrate)."""

    def __init__(self, get_response):
        self.get_response = get_response
        if os.environ.get('VERCEL') and not os.environ.get('VERCEL_BUILD'):
            try:
                ensure_vercel_db()
            except Exception:
                logger.exception('Vercel bootstrap failed on init')

    def __call__(self, request):
        if os.environ.get('VERCEL') and not os.environ.get('VERCEL_BUILD'):
            try:
                ok = ensure_vercel_db()
                if not ok:
                    ensure_vercel_db(force=True)
            except Exception:
                logger.exception('Vercel bootstrap failed on request')
                try:
                    ensure_vercel_db(force=True)
                except Exception:
                    logger.exception('Vercel forced rebuild failed')
        return self.get_response(request)


class VercelHostMiddleware:
    """Додає поточний *.vercel.app хост у CSRF_TRUSTED_ORIGINS і ALLOWED_HOSTS."""

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
