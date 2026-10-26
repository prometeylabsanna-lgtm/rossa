#!/usr/bin/env python3
import os
import sys
from pathlib import Path


def _is_test_command(argv):
    """Чи перша позиційна команда — test (прапорці на кшталт --settings пропускаємо)."""
    skip_next = False
    for arg in argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if arg == '--':
            break
        if arg in {'--settings', '--pythonpath', '--verbosity', '-v'}:
            skip_next = True
            continue
        if arg.startswith('-'):
            continue
        return arg == 'test'
    return False


def main():
    # Лише команда test і лише якщо модуль налаштувань не задали ззовні.
    # --settings Django застосовує пізніше й перекриває це значення.
    # config.settings.test вимикає тісний rate-limit develop (інакше 429).
    if _is_test_command(sys.argv) and 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.test'
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.develop')

    base_dir = Path(__file__).resolve().parent
    src = str(base_dir / 'src')
    if src not in sys.path:
        sys.path.insert(0, src)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            'Django is not installed. Use python3 -m venv .venv && pip install -r requirements.txt'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
