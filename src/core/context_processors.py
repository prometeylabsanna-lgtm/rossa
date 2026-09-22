from pathlib import Path

from catalog.models import Category

from core.models import SiteSettings

_STATIC_ROOT = Path(__file__).resolve().parent / 'static'


def site_globals(request):
    settings = SiteSettings.load()
    nav_categories = (
        Category.objects.filter(is_active=True, parent__isnull=True)
        .prefetch_related('children')
        .order_by('sort', 'id')
    )
    static_v = 0
    if _STATIC_ROOT.exists():
        mtimes = [
            p.stat().st_mtime_ns
            for p in _STATIC_ROOT.rglob('*')
            if p.suffix in {'.css', '.js'}
        ]
        static_v = max(mtimes, default=0)
    return {
        'site_settings': settings,
        'nav_categories': nav_categories,
        'current_language': getattr(request, 'LANGUAGE_CODE', 'uk')[:2],
        'static_v': static_v,
    }
