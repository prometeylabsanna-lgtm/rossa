from catalog.models import Category

from core.models import SiteSettings


def site_globals(request):
    settings = SiteSettings.load()
    nav_categories = (
        Category.objects.filter(is_active=True, parent__isnull=True)
        .prefetch_related('children')
        .order_by('sort', 'id')
    )
    return {
        'site_settings': settings,
        'nav_categories': nav_categories,
        'current_language': getattr(request, 'LANGUAGE_CODE', 'uk')[:2],
    }
