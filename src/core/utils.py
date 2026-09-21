from django.utils.translation import get_language


def localized(obj, field: str, language: str | None = None):
    """Поле *_uk / *_ru з фолбеком на українську."""
    lang = (language or get_language() or 'uk').split('-')[0]
    if lang not in {'uk', 'ru'}:
        lang = 'uk'
    value = getattr(obj, f'{field}_{lang}', None)
    if value not in (None, ''):
        return value
    return getattr(obj, f'{field}_uk', '') or ''
