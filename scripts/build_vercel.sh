#!/usr/bin/env bash
# Збірка артефактів для Vercel (без env на дашборді).
set -euo pipefail

export DJANGO_SETTINGS_MODULE=config.settings.vercel
export VERCEL_BUILD=1
export PYTHONPATH="${PYTHONPATH:-}:src"

python3 manage.py compilemessages --ignore=.venv --ignore=venv || true
python3 manage.py migrate --noinput
python3 manage.py seed_demo
python3 manage.py collectstatic --noinput

# Перевірка схеми демо-БД (інакше адмінка на Vercel падає з «інсталяція БД»).
python3 - <<'PY'
import sqlite3
import sys
from pathlib import Path

db = Path('db.vercel.sqlite3')
required = {
    'auth_user',
    'catalog_category',
    'catalog_product',
    'catalog_characteristic',
    'catalog_productcharacteristic',
    'catalog_productcoloroption',
    'catalog_fabric',
}
if not db.exists():
    print('ERROR: db.vercel.sqlite3 missing after build', file=sys.stderr)
    sys.exit(1)
con = sqlite3.connect(db)
tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
missing = sorted(required - tables)
if missing:
    print('ERROR: missing tables:', ', '.join(missing), file=sys.stderr)
    sys.exit(1)
print('Vercel DB schema OK:', db.stat().st_size, 'bytes')
PY

# CDN-статика Vercel: /media/... → public/media/...
rm -rf public/media
mkdir -p public/media
if [ -d media_demo ] && [ "$(ls -A media_demo 2>/dev/null || true)" ]; then
  cp -a media_demo/. public/media/
fi

python3 - <<'PY'
import sys
from pathlib import Path

required = [
    Path('media_demo/brand/rossa-logo.png'),
    Path('media_demo/brand/contact-map.webp'),
    Path('media_demo/home/craft.jpg'),
    Path('media_demo/home/slides/slide-1.webp'),
    Path('media_demo/home/video/about-showroom.mp4'),
    Path('media_demo/products/milan.webp'),
    Path('public/media/brand/rossa-logo.png'),
    Path('public/media/home/video/about-showroom.mp4'),
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    print('ERROR: missing media after seed/copy:', ', '.join(missing), file=sys.stderr)
    sys.exit(1)
print('Vercel media OK:', sum(1 for _ in Path('media_demo').rglob('*') if _.is_file()), 'files')
PY

echo "Vercel build OK: db.vercel.sqlite3 + media_demo + public/media + staticfiles"
