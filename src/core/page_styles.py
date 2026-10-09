from __future__ import annotations

import re

from django.core.cache import cache
from django.urls import reverse

from core.models_styles import (
    CHROME_STYLE_CACHE_KEY,
    PAGE_STYLES_CACHE_KEY,
    ChromeStyle,
    PageStyle,
    clear_style_cache,
)

_HEX_RE = re.compile(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$')

# (namespace, url_name) → PageStyle.page
_URL_PAGE_MAP: dict[tuple[str | None, str | None], str] = {
    ('core', 'home'): PageStyle.PAGE_HOME,
    ('core', 'about'): PageStyle.PAGE_ABOUT,
    ('core', 'collab'): PageStyle.PAGE_COLLAB,
    ('core', 'contacts'): PageStyle.PAGE_CONTACTS,
    ('core', 'delivery'): PageStyle.PAGE_DELIVERY,
    ('core', 'offer'): PageStyle.PAGE_OFFER,
    ('core', 'privacy'): PageStyle.PAGE_PRIVACY,
    ('core', 'cookies'): PageStyle.PAGE_COOKIES,
    ('catalog', 'index'): PageStyle.PAGE_CATALOG,
    ('catalog', 'category'): PageStyle.PAGE_CATALOG,
    ('catalog', 'product'): PageStyle.PAGE_CATALOG,
    ('catalog', 'search'): PageStyle.PAGE_CATALOG,
}

_PAGE_PREVIEW: dict[str, tuple[str, dict]] = {
    PageStyle.PAGE_HOME: ('core:home', {}),
    PageStyle.PAGE_ABOUT: ('core:about', {}),
    PageStyle.PAGE_COLLAB: ('core:collab', {}),
    PageStyle.PAGE_CONTACTS: ('core:contacts', {}),
    PageStyle.PAGE_DELIVERY: ('core:delivery', {}),
    PageStyle.PAGE_OFFER: ('core:offer', {}),
    PageStyle.PAGE_PRIVACY: ('core:privacy', {}),
    PageStyle.PAGE_COOKIES: ('core:cookies', {}),
    PageStyle.PAGE_CATALOG: ('catalog:index', {}),
}

LEGAL_SLUG_TO_PAGE = {
    'otrymannya': PageStyle.PAGE_DELIVERY,
    'oferta': PageStyle.PAGE_OFFER,
    'privacy': PageStyle.PAGE_PRIVACY,
    'cookies': PageStyle.PAGE_COOKIES,
}

LEGAL_PAGE_DEFAULTS = {
    PageStyle.PAGE_DELIVERY: {
        'slug': 'otrymannya',
        'title_uk': 'Як отримати замовлення',
        'title_ru': 'Как получить заказ',
        'body_uk': '',
    },
    PageStyle.PAGE_OFFER: {
        'slug': 'oferta',
        'title_uk': 'Договір оферти',
        'title_ru': 'Договор оферты',
        'body_uk': '',
    },
    PageStyle.PAGE_PRIVACY: {
        'slug': 'privacy',
        'title_uk': 'Політика конфіденційності',
        'title_ru': 'Политика конфиденциальности',
        'body_uk': '',
    },
    PageStyle.PAGE_COOKIES: {
        'slug': 'cookies',
        'title_uk': 'Політика використання Cookies',
        'title_ru': 'Политика использования Cookies',
        'body_uk': '',
    },
}


def ensure_page_styles() -> int:
    created = 0
    for value, _label in PageStyle.PAGE_CHOICES:
        _, was_created = PageStyle.objects.get_or_create(page=value)
        if was_created:
            created += 1
    if created:
        clear_style_cache()
    return created


def ensure_legal_pages() -> None:
    from core.management.seed_legal_texts import LEGAL_PAGES
    from core.models_content import LegalPage

    seed_by_slug = {
        slug: {
            'title_uk': title_uk,
            'title_ru': title_ru,
            'body_uk': body_uk,
            'body_ru': body_ru,
        }
        for slug, title_uk, title_ru, body_uk, body_ru in LEGAL_PAGES
    }
    for defaults in LEGAL_PAGE_DEFAULTS.values():
        seed = seed_by_slug.get(defaults['slug'], {})
        LegalPage.objects.get_or_create(
            slug=defaults['slug'],
            defaults={
                'title_uk': seed.get('title_uk', defaults['title_uk']),
                'title_ru': seed.get('title_ru', defaults.get('title_ru', '')),
                'body_uk': seed.get('body_uk', defaults.get('body_uk', '')),
                'body_ru': seed.get('body_ru', ''),
                'is_active': True,
            },
        )


def normalize_hex(value: str, *, default: str = '') -> str:
    raw = (value or '').strip()
    if not raw:
        return default
    if not _HEX_RE.match(raw):
        return default
    if len(raw) == 4:
        return f'#{raw[1] * 2}{raw[2] * 2}{raw[3] * 2}'.lower()
    return raw.lower()


def page_preview_url(page: str) -> str:
    tip = _PAGE_PREVIEW.get(page, ('core:home', {}))
    name, kwargs = tip
    try:
        return reverse(name, kwargs=kwargs)
    except Exception:
        return '/'


def resolve_page_key(request) -> str | None:
    match = getattr(request, 'resolver_match', None)
    if match is None:
        return None
    return _URL_PAGE_MAP.get((match.namespace, match.url_name))


def _styles_map() -> dict[str, dict[str, str]]:
    cached = cache.get(PAGE_STYLES_CACHE_KEY)
    if cached is not None:
        return cached
    data: dict[str, dict[str, str]] = {}
    for row in PageStyle.objects.all():
        data[row.page] = {
            'bg': (row.background_color or '').strip(),
            'text': (row.text_color or '').strip(),
            'accent': (row.accent_color or '').strip(),
        }
    cache.set(PAGE_STYLES_CACHE_KEY, data, 300)
    return data


def get_page_style_vars(request) -> dict:
    page = resolve_page_key(request)
    if not page:
        return {'bg': '', 'text': '', 'accent': ''}
    row = _styles_map().get(page, {})
    return {
        'bg': row.get('bg', ''),
        'text': row.get('text', ''),
        'accent': row.get('accent', ''),
    }


def get_chrome_style_vars() -> dict[str, str]:
    cached = cache.get(CHROME_STYLE_CACHE_KEY)
    if cached is not None:
        return cached
    data = ChromeStyle.load().effective()
    cache.set(CHROME_STYLE_CACHE_KEY, data, 300)
    return data
