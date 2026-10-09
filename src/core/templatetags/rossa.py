import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from core.cms_sanitize import sanitize_cms_html
from core.cms_text import ensure_cms_html
from core.images_webp import srcset_from_url, variant_url

register = template.Library()

_ROSSA_RE = re.compile(r'(Rossa)', re.IGNORECASE)


@register.filter
def loc(item, field):
    if item is None:
        return ''
    lang = (get_language() or 'uk').split('-')[0]
    if isinstance(item, dict):
        return item.get(f'{field}_{lang}') or item.get(f'{field}_uk') or item.get(field) or ''
    return getattr(item, f'{field}_{lang}', None) or getattr(item, f'{field}_uk', '') or ''


@register.filter
def uah(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return value
    return f'{number:,}'.replace(',', ' ')


@register.filter(is_safe=True)
def cms_html(value):
    """HTML з TinyMCE → allowlist sanitize → mark_safe. Plain text → абзаци."""
    text = ensure_cms_html(value or '')
    if not text:
        return ''
    return mark_safe(sanitize_cms_html(text))


@register.filter(is_safe=True)
def highlight_rossa(value):
    """Обгортає перше «Rossa» у span.about-band__brand (золотий акцент)."""
    text = escape(value or '')
    if not text:
        return ''
    return mark_safe(_ROSSA_RE.sub(r'<span class="about-band__brand">\1</span>', text, count=1))


@register.filter
def img_variant(url, width=960):
    """URL responsive-варіанту: ontario.webp → ontario_w960.webp."""
    try:
        width_i = int(width)
    except (TypeError, ValueError):
        width_i = 960
    return variant_url(url or '', width_i)


@register.filter
def img_srcset(url):
    """srcset для 640/960/1600w."""
    return srcset_from_url(url or '')
