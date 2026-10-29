from types import SimpleNamespace

from catalog.models import Category, Product
from django.contrib.sitemaps import Sitemap
from django.db.models import Exists, OuterRef
from django.urls import reverse

from core.models import LegalPage
from core.seo import configured_origin


class LocalizedSitemap(Sitemap):
    i18n = True
    alternates = True
    x_default = True

    def get_urls(self, page=1, site=None, protocol=None):
        items = self.items()
        has_items = items.exists() if hasattr(items, 'exists') else bool(items)
        if not has_items:
            return []
        origin = configured_origin()
        if origin is not None:
            scheme, netloc = origin
            site = SimpleNamespace(domain=netloc)
            protocol = scheme
        return super().get_urls(page=page, site=site, protocol=protocol)


class StaticSitemap(LocalizedSitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return [
            'core:home',
            'catalog:index',
            'core:collab',
            'core:about',
            'core:contacts',
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(LocalizedSitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        own = Product.objects.filter(category=OuterRef('pk'), is_active=True)
        nested = Product.objects.filter(
            category__parent=OuterRef('pk'),
            category__is_active=True,
            is_active=True,
        )
        return (
            Category.objects.filter(is_active=True)
            .filter(Exists(own) | Exists(nested))
            .order_by('sort', 'id')
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class ProductSitemap(LocalizedSitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_active=True).order_by('slug')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


LEGAL_URLS = {
    'otrymannya': 'core:delivery',
    'oferta': 'core:offer',
    'privacy': 'core:privacy',
    'cookies': 'core:cookies',
}


class LegalSitemap(LocalizedSitemap):
    changefreq = 'monthly'
    priority = 0.4

    def items(self):
        return LegalPage.objects.filter(is_active=True).order_by('slug')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(LEGAL_URLS.get(obj.slug, 'core:privacy'))


sitemaps = {
    'static': StaticSitemap,
    'categories': CategorySitemap,
    'products': ProductSitemap,
    'legal': LegalSitemap,
}
