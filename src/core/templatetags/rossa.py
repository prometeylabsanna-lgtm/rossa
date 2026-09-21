from django import template
from django.utils.translation import get_language

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
