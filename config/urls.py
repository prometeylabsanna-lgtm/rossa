from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import Http404
from django.urls import include, path, re_path
from django.views.i18n import set_language

from core.admin_upload import cms_upload
from core.sitemaps import sitemaps
from core.views import healthz, robots_txt
from core.views_media import serve_media

_ADMIN = settings.ADMIN_URL


def _legacy_admin_gone(request, rest=None):
    """Старий /admin навмисно віддає 404 (кастомна сторінка через handler404)."""
    raise Http404()


urlpatterns = [
    path(f'{_ADMIN}/cms-upload/', cms_upload, name='cms_upload'),
    path(f'{_ADMIN}/', admin.site.urls),
    re_path(r'^admin(?:/(?P<rest>.*))?$', _legacy_admin_gone),
    path('tinymce/', include('tinymce.urls')),
    path('i18n/setlang/', set_language, name='set_language'),
    path('healthz/', healthz, name='healthz'),
    path('robots.txt', robots_txt, name='robots'),
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
]

urlpatterns += i18n_patterns(
    path('', include('catalog.urls')),
    path('', include('leads.urls')),
    path('', include('core.urls')),
    prefix_default_language=False,
)

handler404 = 'core.views.page_not_found'

# django.conf.urls.static.static() ігнорує все при DEBUG=False — для Vercel реєструємо вручну.
if getattr(settings, 'SERVE_MEDIA', False):
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve_media),
    ]
elif settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
