"""Простий IP rate-limit для публічних lead POST (cache)."""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest

# Вікно / ліміт: захист від спам-ботів, не WAF.
WINDOW_SECONDS = 60
KEY_PREFIX = 'leads:rl:'


def _max_hits() -> int:
    return int(getattr(settings, 'LEAD_RATE_LIMIT_MAX', 10))


def client_ip(request: HttpRequest) -> str:
    forwarded = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0].strip()
    if forwarded:
        return forwarded[:64]
    return (request.META.get('REMOTE_ADDR') or 'unknown')[:64]


def allow_lead_post(request: HttpRequest) -> bool:
    """True — можна приймати; False — ліміт вичерпано."""
    limit = _max_hits()
    if limit <= 0:
        return True
    key = f'{KEY_PREFIX}{client_ip(request)}'
    try:
        hits = cache.incr(key)
    except ValueError:
        cache.add(key, 1, WINDOW_SECONDS)
        return True
    if hits == 1:
        cache.set(key, 1, WINDOW_SECONDS)
    return hits <= limit
