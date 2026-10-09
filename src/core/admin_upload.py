"""Адмін-завантаження зображень для JSON-галерей CMS."""

from __future__ import annotations

import re
from pathlib import Path

from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.images_webp import convert_upload_to_webp

ALLOWED_UPLOAD_PREFIXES = (
    'about/evolution/',
    'about/logos/',
    'about/',
)

_SAFE_NAME = re.compile(r'[^a-zA-Z0-9._-]+')
_ALLOWED_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}


def _safe_upload_to(raw: str) -> str | None:
    value = (raw or '').strip().lstrip('/')
    if not value.endswith('/'):
        value = f'{value}/'
    for prefix in ALLOWED_UPLOAD_PREFIXES:
        if value == prefix or value.startswith(prefix):
            return value
    return None


@staff_member_required
@require_POST
def cms_upload(request):
    upload = request.FILES.get('file')
    if not upload:
        return JsonResponse({'error': 'Файл не передано'}, status=400)

    upload_to = _safe_upload_to(request.POST.get('upload_to', ''))
    if not upload_to:
        return JsonResponse({'error': 'Недозволений шлях завантаження'}, status=400)

    ext = Path(upload.name or '').suffix.lower()
    if ext not in _ALLOWED_EXT:
        return JsonResponse({'error': 'Дозволені лише зображення (jpg, png, webp, gif)'}, status=400)

    if upload.size and upload.size > 8 * 1024 * 1024:
        return JsonResponse({'error': 'Не більше 8 МБ.'}, status=400)

    base = _SAFE_NAME.sub('-', Path(upload.name).stem).strip('-.') or 'image'
    filename = f'{upload_to}{base}{ext}'
    file_obj = upload

    converted = convert_upload_to_webp(filename, upload)
    if converted is not None:
        filename, file_obj = converted

    saved = default_storage.save(filename, file_obj)
    url = default_storage.url(saved)
    return JsonResponse({'url': url, 'path': saved})
