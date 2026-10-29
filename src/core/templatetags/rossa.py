import re

from django import template
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from core.cms_sanitize import sanitize_cms_html
from core.cms_text import ensure_cms_html
from core.images_webp import ensure_webp_beside, image_size, srcset_from_url, variant_url

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


@register.simple_tag
def cms_picture(
    url,
    alt='',
    width=None,
    height=None,
    loading='lazy',
    decoding='async',
    fetchpriority=None,
    img_class='',
):
    """
    <picture> для JSON-шляхів CMS: WebP sibling + fallback на оригінал.
    Оригінал не змінює. width/height — з аргументів або з файлу.
    """
    src = (url or '').strip()
    if not src:
        return ''
    webp = ensure_webp_beside(src)
    w, h = width, height
    if not w or not h:
        size = image_size(src) or (image_size(webp) if webp else None)
        if size:
            w = w or size[0]
            h = h or size[1]
    attrs = []
    if img_class:
        attrs.append(format_html(' class="{}"', img_class))
    if w:
        attrs.append(format_html(' width="{}"', w))
    if h:
        attrs.append(format_html(' height="{}"', h))
    if loading:
        attrs.append(format_html(' loading="{}"', loading))
    if decoding:
        attrs.append(format_html(' decoding="{}"', decoding))
    if fetchpriority:
        attrs.append(format_html(' fetchpriority="{}"', fetchpriority))
    extra = mark_safe(''.join(attrs))
    alt_text = alt or ''
    if webp and webp != src:
        return format_html(
            '<picture><source type="image/webp" srcset="{}"><img src="{}" alt="{}"{}></picture>',
            webp,
            src,
            alt_text,
            extra,
        )
    return format_html('<img src="{}" alt="{}"{}>', src, alt_text, extra)
