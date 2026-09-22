#!/usr/bin/env bash
# Збірка артефактів для Vercel (без env на дашборді).
set -euo pipefail

export DJANGO_SETTINGS_MODULE=config.settings.vercel
export VERCEL_BUILD=1
export PYTHONPATH="${PYTHONPATH:-}:src"

python3 manage.py migrate --noinput
python3 manage.py seed_demo
python3 manage.py collectstatic --noinput

echo "Vercel build OK: db.vercel.sqlite3 + media_demo + staticfiles"
