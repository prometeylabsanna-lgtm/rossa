"""
WSGI entrypoint для Vercel Serverless.

Експортує `app` — так очікує @vercel/python для WSGI.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.vercel')

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
