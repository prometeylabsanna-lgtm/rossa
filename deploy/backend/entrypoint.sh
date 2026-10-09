#!/bin/sh
set -e
python scripts/build_css_bundles.py
python manage.py migrate --noinput
python manage.py compilemessages || true
python manage.py collectstatic --noinput
exec "$@"
