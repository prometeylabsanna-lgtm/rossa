from catalog.models import Category
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET
from leads.forms import ContactForm, PartnershipForm

from core.models import AboutPage, CollabPage, HomePage, LegalPage, SiteSettings, ValueProp


def _seo(request, title, description, image=None):
    canonical = request.build_absolute_uri(request.path)
    return {
        'seo_title': title,
        'seo_description': description,
        'canonical_url': canonical,
        'og_image': image,
    }


@require_GET
def healthz(request):
    return HttpResponse('ok')


@require_GET
def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse('django.contrib.sitemaps.views.sitemap'))
    body = f'User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {sitemap_url}\n'
    return HttpResponse(body, content_type='text/plain')


def page_not_found(request, exception):
    return render(request, 'pages/404.html', status=404)


def home(request):
    page = HomePage.load()
    settings = SiteSettings.load()
    categories = (
        Category.objects.filter(is_active=True, parent__isnull=True)
        .order_by('sort', 'id')
    )
    from catalog.selectors import home_featured
    context = {
        'page': page,
        'value_props': ValueProp.objects.filter(is_active=True),
        'featured_categories': categories,
        'bestsellers': home_featured()[:6],
        **_seo(
            request,
            page.seo_title or 'ROSSA — м’які меблі',
            page.seo_description or page.hero_sub,
            page.hero_poster.url if page.hero_poster else (settings.logo.url if settings.logo else None),
        ),
    }
    return render(request, 'pages/home.html', context)


def about(request):
    page = AboutPage.load()
    return render(request, 'pages/about.html', {
        'page': page,
        'breadcrumbs': [
            {'label': _('Головна'), 'url': '/', 'has_next': True},
            {'label': page.title, 'url': None, 'has_next': False},
        ],
        **_seo(request, page.seo_title or page.title, page.seo_description or (page.body or '')[:160]),
    })


def collab(request):
    page = CollabPage.load()
    return render(request, 'pages/collab.html', {
        'page': page,
        'form': PartnershipForm(),
        'breadcrumbs': [
            {'label': _('Головна'), 'url': '/', 'has_next': True},
            {'label': page.title, 'url': None, 'has_next': False},
        ],
        **_seo(request, page.seo_title or page.title, page.seo_description or (page.sub or '')[:160]),
    })


def contacts(request):
    settings = SiteSettings.load()
    return render(request, 'pages/contacts.html', {
        'form': ContactForm(),
        'map_image': settings.map_image,
        'breadcrumbs': [
            {'label': _('Головна'), 'url': '/', 'has_next': True},
            {'label': _('Контакти'), 'url': None, 'has_next': False},
        ],
        **_seo(
            request,
            _('Контакти — ROSSA'),
            f'{settings.phone}. {settings.address}. {settings.hours}.',
        ),
    })


def thanks(request):
    return render(request, 'pages/thanks.html', {
        **_seo(request, _('Дякуємо за заявку — ROSSA'), _('Менеджер зв’яжеться з вами найближчим часом.')),
    })


def legal(request, slug):
    page = get_object_or_404(LegalPage, slug=slug, is_active=True)
    return render(request, 'pages/legal.html', {
        'page': page,
        'breadcrumbs': [
            {'label': _('Головна'), 'url': '/', 'has_next': True},
            {'label': page.title, 'url': None, 'has_next': False},
        ],
        **_seo(request, page.seo_title or page.title, page.seo_description or (page.body or '')[:160]),
    })
