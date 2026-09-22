#!/usr/bin/env bash
# Збірка артефактів для Vercel (без env на дашборді).
set -euo pipefail

export DJANGO_SETTINGS_MODULE=config.settings.vercel
export VERCEL_BUILD=1
export PYTHONPATH="${PYTHONPATH:-}:src"

python3 manage.py migrate --noinput
python3 manage.py seed_demo
python3 manage.py collectstatic --noinput

# CDN-статика Vercel: /media/... → public/media/...
rm -rf public/media
mkdir -p public/media
if [ -d media_demo ] && [ "$(ls -A media_demo 2>/dev/null || true)" ]; then
  cp -a media_demo/. public/media/
fi

echo "Vercel build OK: db.vercel.sqlite3 + media_demo + public/media + staticfiles"
