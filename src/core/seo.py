"""Canonical, robots, hreflang і absolute URL через settings.SITE_URL."""

from __future__ import annotations

import re
from html import unescape
from urllib.parse import urlsplit

from django.conf import settings
from django.urls import translate_url
from django.utils.translation import get_language

TITLE_MAX = 60
DESCRIPTION_MAX = 160
ELLIPSIS = '…'
BRAND = 'ROSSA'
BRAND_SUFFIX = f' | {BRAND}'
_HIDDEN_BLOCK = re.compile(r'<(script|style)\b[^>]*>.*?</\1>', re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r'<[^>]+>')
_TRAILING = ' .,;:—-–'
_BRAND_TRAIL = re.compile(r'\s*[|—–\-]\s*ROSSA\s*$', re.IGNORECASE)
_BRAND_LEAD = re.compile(r'^ROSSA\s*[|—–\-]\s*', re.IGNORECASE)

NOINDEX_URL_NAMES = frozenset({'thanks', 'search'})
CATALOG_URL_NAMES = frozenset({'index', 'category'})
PRODUCT_URL_NAMES = frozenset({'product'})
DEFAULT_SORT = 'popular'

# Службові префікси (без шляху адмінки — його закриває X-Robots-Tag).
PRIVATE_PREFIXES = (
    '/poshuk/',
    '/dyakuyemo/',
    '/i18n/',
    '/tinymce/',
    '/healthz/',
)

# Query-параметри каталогу / пошу з views.
FILTER_QUERY_NAMES = (
    'sort',
    'price_min',
    'price_max',
    'available',
    'cat',
    'offset',
    'q',
)
PRODUCT_CONFIG_QUERY_NAMES = ('fabric', 'color', 'shade')

_RESERVED_EMAIL_DOMAINS = ('example.com', 'example.org', 'example.net')
_FAKE_EMAIL_SUFFIXES = ('.local', '.example', '.test')
_EMPTY_CONTACTS = {
    'phone': '',
    'email': '',
    'address': '',
    'addresses': (),
    'same_as': (),
}


def plain_text(value) -> str:
    raw = _HIDDEN_BLOCK.sub(' ', str(value or ''))
    raw = _TAG.sub(' ', raw)
    return ' '.join(unescape(raw).split())


_NATIONWIDE_DELIVERY = (
    (re.compile(r'доставка\s+по\s+всій\s+Україні', re.IGNORECASE), 'uk'),
    (re.compile(r'доставка\s+по\s+всей\s+Украине', re.IGNORECASE), 'ru'),
    (re.compile(r'доставка\s+по\s+Україні', re.IGNORECASE), 'uk'),
    (re.compile(r'доставка\s+по\s+Украине', re.IGNORECASE), 'ru'),
    (re.compile(r'delivery\s+across\s+Ukraine', re.IGNORECASE), 'uk'),
)


def pickup_phrase(*, lang: str | None = None) -> str:
    """Текст самовивозу з SiteSettings.delivery_label або коротке «самовивіз»."""
    code = (lang or get_language() or 'uk')[:2]
    label = ''
    try:
        from django.db.utils import OperationalError, ProgrammingError

        from core.models import SiteSettings

        site = SiteSettings.load()
        attr = 'delivery_label_ru' if code == 'ru' else 'delivery_label_uk'
        label = ' '.join(str(getattr(site, attr, '') or '').split())
        if not label:
            label = ' '.join(str(getattr(site, 'delivery_label', '') or '').split())
    except (OperationalError, ProgrammingError, AttributeError):
        label = ''
    if label:
        return label
    return 'самовывоз' if code == 'ru' else 'самовивіз'


def rewrite_nationwide_delivery(value: str, *, lang: str | None = None) -> str:
    """Замінює SEO-фрази про доставку по Україні на самовивіз (без вигаданої адреси)."""
    text = str(value or '')
    if not text:
        return text
    code = (lang or get_language() or 'uk')[:2]
    pickup = pickup_phrase(lang=code)
    mid = pickup[:1].lower() + pickup[1:] if pickup else pickup
    updated = text
    for pattern, _lang in _NATIONWIDE_DELIVERY:
        updated = pattern.sub(mid, updated)
    return updated


def _splits_word(text: str, index: int) -> bool:
    if index <= 0 or index >= len(text):
        return False
    return text[index - 1].isalnum() and text[index].isalnum()


def clip_text(value, limit: int) -> str:
    text = plain_text(value)
    if limit <= 0 or not text:
        return ''
    if len(text) <= limit:
        return text
    if limit <= len(ELLIPSIS):
        return ELLIPSIS[:limit]
    budget = limit - len(ELLIPSIS)
    trimmed = text[:budget]
    if _splits_word(text, budget) and ' ' in trimmed:
        trimmed = trimmed.rsplit(' ', 1)[0]
    trimmed = trimmed.rstrip(_TRAILING)
    if not trimmed:
        return ELLIPSIS
    return trimmed + ELLIPSIS


def strip_brand(value) -> str:
    """Прибирає провідний/кінцевий бренд із title (—, |, -)."""
    text = plain_text(value)
    if not text:
        return ''
    if text.upper() == BRAND:
        return ''
    text = _BRAND_TRAIL.sub('', text)
    text = _BRAND_LEAD.sub('', text)
    text = text.strip(_TRAILING + ' ')
    if text.upper() == BRAND:
        return ''
    return text


def branded_title(value) -> str:
    """
    Title з суфіксом « | ROSSA». Довжина ≤ TITLE_MAX за рахунок обрізання
    основної частини; бренд ніколи не обрізається.
    """
    main = strip_brand(value)
    if not main:
        return BRAND
    budget = TITLE_MAX - len(BRAND_SUFFIX)
    if budget < 1:
        return BRAND
    main = clip_text(main, budget)
    if not main:
        return BRAND
    return f'{main}{BRAND_SUFFIX}'


def configured_origin() -> tuple[str, str] | None:
    raw = str(getattr(settings, 'SITE_URL', '') or '').strip()
    if not raw:
        return None
    if '://' not in raw:
        raw = 'https://' + raw.lstrip('/')
    parts = urlsplit(raw)
    if not parts.netloc:
        return None
    return (parts.scheme or 'https', parts.netloc)


def public_base(request=None) -> str:
    origin = configured_origin()
    if origin is not None:
        scheme, netloc = origin
        return f'{scheme}://{netloc}'
    if request is not None:
        return f'{request.scheme}://{request.get_host()}'
    return ''


def absolute_url(path: str, request=None) -> str:
    value = str(path or '').strip()
    if not value:
        return public_base(request)
    if value.startswith(('http://', 'https://')):
        return value
    if not value.startswith('/'):
        value = '/' + value
    return public_base(request) + value


def absolute_media(request, url: str) -> str:
    value = str(url or '').strip()
    if not value:
        return ''
    if value.startswith(('http://', 'https://')):
        return value
    if not value.startswith('/'):
        value = '/' + value
    return public_base(request) + value


def _url_name(request) -> str:
    match = getattr(request, 'resolver_match', None)
    if match is None:
        return ''
    return match.url_name or ''


def _is_tracking(key: str) -> bool:
    return key == 'utm' or key.startswith('utm_')


def _query_extras(request) -> list[str]:
    extras = []
    for key in request.GET.keys():
        if _is_tracking(key):
            continue
        if key == 'sort' and (request.GET.get('sort') or DEFAULT_SORT) == DEFAULT_SORT:
            continue
        extras.append(key)
    return extras


def _indexable(request, url_name: str, extras: list[str]) -> bool:
    if getattr(request, 'seo_noindex', False):
        return False
    if getattr(request, 'resolver_match', None) is None:
        return False
    if url_name in NOINDEX_URL_NAMES:
        return False
    if url_name in CATALOG_URL_NAMES and extras:
        return False
    if url_name in PRODUCT_URL_NAMES and any(
        key in PRODUCT_CONFIG_QUERY_NAMES for key in extras
    ):
        return False
    if extras and url_name == 'search':
        return False
    return True


def hreflang_alternates(request, *, indexable: bool) -> list[dict]:
    if not indexable:
        return []
    base = public_base(request)
    path = request.path
    links = []
    default_href = ''
    for code, _label in settings.LANGUAGES:
        href = base + translate_url(path, code)
        links.append({'code': code, 'href': href})
        if code == settings.LANGUAGE_CODE:
            default_href = href
    if default_href:
        links.append({'code': 'x-default', 'href': default_href})
    return links


def build_head(request) -> dict:
    """Canonical / robots / hreflang для будь-якої публічної сторінки."""
    url_name = _url_name(request)
    extras = _query_extras(request)
    indexable = _indexable(request, url_name, extras)
    canonical = absolute_url(request.path, request)
    robots = '' if indexable else 'noindex,follow'
    return {
        'canonical': canonical,
        'robots': robots,
        'alternates': hreflang_alternates(request, indexable=indexable),
        'indexable': indexable,
        'og_locale': 'ru_RU' if (get_language() or 'uk')[:2] == 'ru' else 'uk_UA',
        'og_type': 'product' if url_name == 'product' else 'website',
    }


def page_seo(
    request,
    title: str,
    description: str,
    *,
    image: str | None = None,
    noindex: bool | None = None,
) -> dict:
    """Контекст meta для views (сумісний із наявними шаблонами)."""
    head = build_head(request)
    if noindex is True:
        head['robots'] = 'noindex,follow'
        head['indexable'] = False
        head['alternates'] = []
    title_text = branded_title(title)
    desc_text = clip_text(rewrite_nationwide_delivery(description), DESCRIPTION_MAX)
    og = image or ''
    if og and not og.startswith(('http://', 'https://')):
        og = absolute_media(request, og)
    return {
        'seo_title': title_text,
        'seo_description': desc_text,
        'canonical_url': head['canonical'],
        'og_image': og or None,
        'noindex': not head['indexable'],
        'seo_robots': head['robots'],
        'hreflang_links': head['alternates'],
        'og_locale': head['og_locale'],
        'og_type': head['og_type'],
        'seo_indexable': head['indexable'],
    }


def catalog_filter_query_names() -> tuple[str, ...]:
    return FILTER_QUERY_NAMES


def robots_text(request=None) -> str:
    """Динамічний robots.txt. Шлях адмінки навмисно не згадується."""
    base = public_base(request)
    disallow_lines: list[str] = []
    for prefix in PRIVATE_PREFIXES:
        disallow_lines.append(f'Disallow: {prefix}')
    for code, _label in settings.LANGUAGES:
        if code == settings.LANGUAGE_CODE:
            continue
        for prefix in PRIVATE_PREFIXES:
            disallow_lines.append(f'Disallow: /{code}{prefix}')
    # Фільтри каталогу (sort/price/…): noindex у HTML, без Disallow у robots.
    disallow_lines.append('Disallow: /*?*utm_')

    blocks: list[str] = []
    for agent in ('Googlebot', 'Bingbot', '*'):
        blocks.append(f'User-agent: {agent}')
        blocks.append('Allow: /')
        blocks.extend(disallow_lines)
        blocks.append('')
    blocks.append(f'Sitemap: {base}/sitemap.xml')
    blocks.append('')
    return '\n'.join(blocks)


def is_placeholder_contact(value: str, kind: str) -> bool:
    raw = str(value or '').strip()
    if kind == 'phone':
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if not digits or set(digits) == {'0'}:
            return True
        if digits.startswith('380'):
            national = digits[3:]
            if not national or set(national) == {'0'}:
                return True
        return False
    if kind == 'email':
        if '@' not in raw:
            return True
        domain = raw.rsplit('@', 1)[1].lower().rstrip('.')
        if not domain or domain.endswith(_FAKE_EMAIL_SUFFIXES):
            return True
        return any(domain == name or domain.endswith('.' + name) for name in _RESERVED_EMAIL_DOMAINS)
    return not raw


def public_contacts() -> dict:
    try:
        from django.db.utils import OperationalError, ProgrammingError

        from core.models import SiteSettings

        site = SiteSettings.load()
    except (OperationalError, ProgrammingError, AttributeError):
        return dict(_EMPTY_CONTACTS)

    phones = []
    for value in (site.phone, site.phone_2, site.phone_3):
        phone = ' '.join(str(value or '').split())
        if phone and not is_placeholder_contact(phone, 'phone'):
            phones.append(phone)
    email = str(site.email or '').strip()
    if is_placeholder_contact(email, 'email'):
        email = ''
    addresses = []
    for code in ('uk', 'ru'):
        text = ' '.join(str(getattr(site, f'address_{code}', '') or '').split())
        if text and text not in addresses:
            addresses.append(text)
    same = []
    for attr in ('instagram_url', 'facebook_url', 'telegram_url', 'tiktok_url'):
        value = str(getattr(site, attr, '') or '').strip()
        if value:
            same.append(value)
    return {
        'phone': phones[0] if phones else '',
        'phones': tuple(phones),
        'email': email,
        'address': addresses[0] if addresses else '',
        'addresses': tuple(addresses),
        'same_as': tuple(same),
    }


def category_meta_description(category) -> str:
    custom = plain_text(getattr(category, 'seo_description', '') or '')
    if custom:
        return rewrite_nationwide_delivery(custom)
    name = plain_text(getattr(category, 'name', '') or '')
    return clip_text(
        f'{name} — м’які меблі власного виробництва ROSSA. Обирайте тканину та відтінок.',
        DESCRIPTION_MAX,
    )


def product_meta_description(product) -> str:
    custom = plain_text(getattr(product, 'seo_description', '') or '')
    if custom:
        return rewrite_nationwide_delivery(custom)
    desc = plain_text(getattr(product, 'description', '') or '')
    if desc:
        return clip_text(rewrite_nationwide_delivery(desc), DESCRIPTION_MAX)
    name = plain_text(getattr(product, 'name', '') or '')
    cat = ''
    if getattr(product, 'category_id', None):
        cat = plain_text(product.category.name)
    parts = [p for p in (name, cat, 'м’які меблі ROSSA') if p]
    return clip_text('. '.join(parts), DESCRIPTION_MAX)
