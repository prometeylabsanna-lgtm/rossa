import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

BASE_DIR = Path(__file__).resolve().parent.parent
src = str(BASE_DIR / 'src')
if src not in sys.path:
    sys.path.insert(0, src)

if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    if os.environ.get('VERCEL'):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.vercel'
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

application = get_wsgi_application()

# Сумісність із деякими Python-адаптерами Vercel
app = application
