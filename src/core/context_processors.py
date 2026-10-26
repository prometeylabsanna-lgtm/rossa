import re
from pathlib import Path

from catalog.models import Category
from csp.constants import NONCE
from django.conf import settings as django_settings
from django.db.models import Prefetch
from django.urls import translate_url

from core.models import SiteSettings
from core.page_styles import get_chrome_style_vars, get_page_style_vars

_STATIC_ROOT = Path(__file__).resolve().parent / 'static'
_GTM_ID_RE = re.compile(r'^GTM-[A-Z0-9]+$')


def _language_switch_urls(request) -> dict[str, str]:
    """URL тієї ж сторінки іншою мовою (без POST/CSRF)."""
    full_path = request.get_full_path()
    current = getattr(request, 'LANGUAGE_CODE', 'uk')[:2]
    urls: dict[str, str] = {}
    for code, _label in django_settings.LANGUAGES:
        if code == current:
            urls[code] = full_path
        else:
            urls[code] = translate_url(full_path, code)
    return urls


def _contains_csp_nonce(value) -> bool:
    if value is NONCE:
        return True
    if isinstance(value, (str, bytes)) or value is None:
        return False
    try:
        return any(item is NONCE for item in value)
    except TypeError:
        return False


def _policy_uses_script_nonce(policy) -> bool:
    if not isinstance(policy, dict):
        return False
    directives = policy.get('DIRECTIVES') or {}
    return any(
        _contains_csp_nonce(directives.get(name))
        for name in ('script-src', 'script-src-elem')
    )


def gtm(_request):
    """GTM_ID для публічного base.html. Nonce лише якщо CSP його вимагає."""
    raw = getattr(django_settings, 'GTM_ID', '') or ''
    gtm_id = raw.strip() if isinstance(raw, str) else ''
    if not _GTM_ID_RE.fullmatch(gtm_id):
        gtm_id = ''
    uses_nonce = _policy_uses_script_nonce(
        getattr(django_settings, 'CONTENT_SECURITY_POLICY', None),
    ) or _policy_uses_script_nonce(
        getattr(django_settings, 'CONTENT_SECURITY_POLICY_REPORT_ONLY', None),
    )
    return {
        'GTM_ID': gtm_id,
        'GTM_USE_NONCE': uses_nonce,
    }


def site_globals(request):
    settings = SiteSettings.load()
    active_children = Prefetch(
        'children',
        queryset=Category.objects.filter(is_active=True).order_by('sort', 'id'),
    )
    nav_categories = (
        Category.objects.filter(is_active=True, parent__isnull=True)
        .prefetch_related(active_children)
        .order_by('sort', 'id')
    )
    static_v = 0
    if _STATIC_ROOT.exists():
        mtimes = [
            p.stat().st_mtime_ns
            for p in _STATIC_ROOT.rglob('*')
            if p.suffix in {'.css', '.js', '.woff2', '.webp'}
        ]
        static_v = max(mtimes, default=0)
    return {
        'site_settings': settings,
        'nav_categories': nav_categories,
        'current_language': getattr(request, 'LANGUAGE_CODE', 'uk')[:2],
        'lang_urls': _language_switch_urls(request),
        'static_v': static_v,
        'page_style': get_page_style_vars(request),
        'chrome_style': get_chrome_style_vars(),
    }
