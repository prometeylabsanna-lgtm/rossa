from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.i18n import set_language

from core.sitemaps import sitemaps
from core.views import healthz, robots_txt

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/setlang/', set_language, name='set_language'),
    path('healthz/', healthz, name='healthz'),
    path('robots.txt', robots_txt, name='robots'),
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    path('', include('catalog.urls')),
    path('', include('leads.urls')),
    path('', include('core.urls')),
]

handler404 = 'core.views.page_not_found'

if settings.DEBUG or getattr(settings, 'SERVE_MEDIA', False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
