"""Примусова українська мова для Django/Unfold admin."""
from __future__ import annotations

from django.conf import settings
from django.utils import translation


def _is_admin_path(path: str) -> bool:
    prefix = f'/{settings.ADMIN_URL.strip("/")}'
    return path == prefix or path.startswith(f'{prefix}/')


class AdminForceUkrainianMiddleware:
    """Адмінка завжди українською, незалежно від мови вітрини."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if _is_admin_path(request.path):
            translation.activate('uk')
            request.LANGUAGE_CODE = 'uk'
        response = self.get_response(request)
        if _is_admin_path(request.path):
            response['Content-Language'] = 'uk'
        return response
