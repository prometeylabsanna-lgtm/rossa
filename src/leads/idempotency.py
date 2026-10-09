"""Ідемпотентність публічних lead POST (захист від подвійного кліку)."""

from __future__ import annotations

import secrets

from django.core.cache import cache

TTL_SECONDS = 60 * 60
KEY_PREFIX = 'leads:idem:'


def new_idempotency_key() -> str:
    return secrets.token_urlsafe(18)


def _cache_key(token: str) -> str:
    return f'{KEY_PREFIX}{token}'


def claim_idempotency_key(token: str) -> bool:
    """True — перший успішний claim; False — дублікат або невалідний токен."""
    token = (token or '').strip()
    if not token or len(token) > 64:
        return False
    return cache.add(_cache_key(token), 'claimed', TTL_SECONDS)


def release_idempotency_key(token: str) -> None:
    """Дозволяє повтор після збою збереження."""
    token = (token or '').strip()
    if not token:
        return
    cache.delete(_cache_key(token))
