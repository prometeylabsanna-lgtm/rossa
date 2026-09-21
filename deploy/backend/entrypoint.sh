#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py compilemessages || true
python manage.py collectstatic --noinput
exec "$@"
