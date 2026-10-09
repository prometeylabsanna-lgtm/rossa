#!/usr/bin/env bash
# Збірка артефактів для Vercel (без env на дашборді).
set -euo pipefail

export DJANGO_SETTINGS_MODULE=config.settings.vercel
export VERCEL_BUILD=1
export PYTHONPATH="${PYTHONPATH:-}:src"

python3 scripts/build_css_bundles.py
python3 manage.py compilemessages --ignore=.venv --ignore=venv || true
python3 manage.py migrate --noinput
python3 manage.py seed_demo
# Оптимізація демо-медіа (resize + variants) перед копіюванням у public/
python3 manage.py optimize_media --root media_demo
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

# about-showroom.mp4 більше не сідиться: HomePage.about_video прибрано (0018).
# WebPImageField при seed конвертує png/jpg → .webp (див. core.fields.WebPImageField).
def require_any(*candidates: Path) -> Path | None:
    for path in candidates:
        if path.exists():
            return path
    return None


checks = [
    ('logo', Path('media_demo/brand/rossa-logo.webp'), Path('media_demo/brand/rossa-logo.png')),
    ('map', Path('media_demo/brand/contact-map.webp')),
    ('craft', Path('media_demo/home/craft.webp'), Path('media_demo/home/craft.jpg')),
    ('slide', Path('media_demo/home/slides/slide-1.webp')),
    ('product', Path('media_demo/products/milan.webp')),
    ('public-logo', Path('public/media/brand/rossa-logo.webp'), Path('public/media/brand/rossa-logo.png')),
    ('public-slide', Path('public/media/home/slides/slide-1.webp')),
]
missing = []
for label, *candidates in checks:
    if require_any(*candidates) is None:
        missing.append(f'{label} ({" | ".join(str(c) for c in candidates)})')
if missing:
    print('ERROR: missing media after seed/copy:', ', '.join(missing), file=sys.stderr)
    sys.exit(1)
print('Vercel media OK:', sum(1 for _ in Path('media_demo').rglob('*') if _.is_file()), 'files')
PY

echo "Vercel build OK: db.vercel.sqlite3 + media_demo + public/media + staticfiles"
