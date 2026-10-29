from catalog.models import Category
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET
from leads.forms import ContactForm, PartnershipForm

from core.models import AboutPage, CollabPage, ContactsPage, HomePage, LegalPage, SiteSettings, ValueProp
from core.seo import page_seo, plain_text, robots_text


def _seo(request, title, description, image=None, *, noindex=None):
    return page_seo(request, title, description, image=image, noindex=noindex)


@require_GET
def healthz(request):
    """Liveness probe."""
    return HttpResponse('ok')


@require_GET
def robots_txt(request):
    return HttpResponse(robots_text(request), content_type='text/plain; charset=utf-8')


@require_GET
def llms_txt(request):
    from core.seo_llms import llms_text

    return HttpResponse(llms_text(request), content_type='text/plain; charset=utf-8')


@require_GET
def llm_txt(request):
    return HttpResponsePermanentRedirect(reverse('llms'))


def page_not_found(request, exception):
    request.seo_noindex = True
    ctx = _seo(
        request,
        _('Сторінку не знайдено'),
        _('Запитуваної сторінки не існує. Перейдіть на головну або до каталогу.'),
        noindex=True,
    )
    return render(request, 'pages/404.html', ctx, status=404)


def home(request):
    page = HomePage.load()
    settings_obj = SiteSettings.load()
    categories = (
        Category.objects.filter(is_active=True, parent__isnull=True)
        .order_by('sort', 'id')
    )
    from catalog.selectors import home_featured
    hero_slides = list(page.hero_slides.filter(is_active=True).order_by('sort', 'id'))
    first_slide = hero_slides[0] if hero_slides else None
    og = None
    if first_slide and first_slide.image:
        og = first_slide.image.url
    elif settings_obj.logo:
        og = settings_obj.logo.url
    title = page.seo_title or 'м’які меблі власного виробництва'
    description = page.seo_description or (
        'Дивани, ліжка та пуфи ROSSA. Власне виробництво в Україні, вибір тканин і індивідуальний підхід.'
    )
    context = {
        'page': page,
        'hero_slides': hero_slides,
        'value_props': ValueProp.objects.filter(is_active=True),
        'featured_categories': categories,
        'bestsellers': home_featured()[:6],
        'home_h1': plain_text(page.seo_title) or 'ROSSA — м’які меблі',
        **_seo(request, title, description, og),
    }
    return render(request, 'pages/home.html', context)


def about(request):
    page = AboutPage.load()
    body_plain = plain_text(page.body or '')
    description = page.seo_description or body_plain[:160] or page.title
    return render(request, 'pages/about.html', {
        'page': page,
        'breadcrumbs': [
            {'label': _('Головна'), 'url': reverse('core:home'), 'has_next': True},
            {'label': page.title, 'url': None, 'has_next': False},
        ],
        **_seo(request, page.seo_title or page.title, description),
    })


def collab(request):
    page = CollabPage.load()
    description = page.seo_description or page.title or _(
        'Партнерство з ROSSA для салонів і дизайнерів.'
    )
    return render(request, 'pages/collab.html', {
        'page': page,
        'form': PartnershipForm(page=page),
        'breadcrumbs': [
            {'label': _('Головна'), 'url': reverse('core:home'), 'has_next': True},
            {'label': page.title, 'url': None, 'has_next': False},
        ],
        **_seo(request, page.seo_title or page.title, description),
    })


def contacts(request):
    settings_obj = SiteSettings.load()
    page = ContactsPage.load()
    fallback = ' '.join(
        part for part in (settings_obj.phone, settings_obj.address, settings_obj.hours) if part
    )
    return render(request, 'pages/contacts.html', {
        'page': page,
        'form': ContactForm(),
        'map_image': settings_obj.map_image,
        'breadcrumbs': [
            {'label': _('Головна'), 'url': reverse('core:home'), 'has_next': True},
            {'label': page.title or _('Контакти'), 'url': None, 'has_next': False},
        ],
        **_seo(
            request,
            page.seo_title or page.title or _('Контакти'),
            page.seo_description or fallback or _('Контакти салону ROSSA.'),
        ),
    })


def thanks(request):
    return render(request, 'pages/thanks.html', {
        **_seo(
            request,
            _('Дякуємо за заявку'),
            _('Менеджер зв’яжеться з вами найближчим часом.'),
            noindex=True,
        ),
    })


def legal(request, slug):
    page = get_object_or_404(LegalPage, slug=slug, is_active=True)
    body_plain = plain_text(page.body or '')
    description = page.seo_description or body_plain[:160] or page.title
    return render(request, 'pages/legal.html', {
        'page': page,
        'breadcrumbs': [
            {'label': _('Головна'), 'url': reverse('core:home'), 'has_next': True},
            {'label': page.title, 'url': None, 'has_next': False},
        ],
        **_seo(request, page.seo_title or page.title, description),
    })
