#!/usr/bin/env python3
import os
import sys
from pathlib import Path


def main():
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.develop'),
    )
    base_dir = Path(__file__).resolve().parent
    src = str(base_dir / 'src')
    if src not in sys.path:
        sys.path.insert(0, src)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError('Django is not installed. Use python3 -m venv .venv && pip install -r requirements.txt') from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
