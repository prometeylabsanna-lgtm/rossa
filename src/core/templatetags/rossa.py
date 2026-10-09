from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from core.cms_sanitize import sanitize_cms_html
from core.cms_text import ensure_cms_html

register = template.Library()


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
