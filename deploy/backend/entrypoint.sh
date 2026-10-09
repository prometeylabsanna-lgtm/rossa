#!/bin/sh
set -e
python scripts/build_css_bundles.py
python manage.py migrate --noinput
python manage.py compilemessages || true
python manage.py collectstatic --noinput
# Docker media_volume не в git — досіюємо craft-фото «Про нас» зі slots.
python manage.py ensure_about_media --force || true
exec "$@"