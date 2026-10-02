"""Примусова українська мова для Django/Unfold admin."""
from __future__ import annotations

from django.utils import translation


class AdminForceUkrainianMiddleware:
    """Адмінка завжди українською, незалежно від мови вітрини."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin'):
            translation.activate('uk')
            request.LANGUAGE_CODE = 'uk'
        response = self.get_response(request)
        if request.path.startswith('/admin'):
            response['Content-Language'] = 'uk'
        return response
