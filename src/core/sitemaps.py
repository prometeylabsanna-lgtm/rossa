from catalog.models import Category, Product
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from core.models import LegalPage


class StaticSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    i18n = True
    alternates = True

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


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    i18n = True
    alternates = True

    def items(self):
        return Category.objects.filter(is_active=True).order_by('sort', 'id')

    def location(self, obj):
        return obj.get_absolute_url()


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9
    i18n = True
    alternates = True

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


class LegalSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.4
    i18n = True
    alternates = True

    def items(self):
        return LegalPage.objects.filter(is_active=True).order_by('slug')

    def location(self, obj):
        return reverse(LEGAL_URLS.get(obj.slug, 'core:privacy'))


sitemaps = {
    'static': StaticSitemap,
    'categories': CategorySitemap,
    'products': ProductSitemap,
    'legal': LegalSitemap,
}
