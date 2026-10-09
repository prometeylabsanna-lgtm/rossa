"""Роздача /media/ з кількох коренів (Vercel: /tmp + media_demo)."""
from __future__ import annotations

import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.views.static import serve as static_serve

# Python <3.13 інколи не знає webp/avif.
mimetypes.add_type('image/webp', '.webp')
mimetypes.add_type('image/avif', '.avif')

_CACHE_IMMUTABLE = 'public, max-age=31536000, immutable'


def serve_media(request, path: str):
    roots: list[Path] = []
    media_root = Path(settings.MEDIA_ROOT)
    roots.append(media_root)

    packaged = getattr(settings, 'MEDIA_PACKAGED_ROOT', None)
    if packaged:
        packaged_path = Path(packaged)
        if packaged_path.resolve() != media_root.resolve():
            roots.append(packaged_path)

    safe = Path(path)
    if safe.is_absolute() or '..' in safe.parts:
        raise Http404('media')

    for root in roots:
        candidate = (root / safe).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            continue
        if not candidate.is_file():
            continue

        content_type, _encoding = mimetypes.guess_type(str(candidate))
        if not content_type:
            # Fallback для webp, якщо mimetypes мовчить.
            if candidate.suffix.lower() == '.webp':
                content_type = 'image/webp'
            else:
                content_type = 'application/octet-stream'

        # long-cache: імена файлів версіонуються через CMS / rebuild.
        response = FileResponse(candidate.open('rb'), content_type=content_type)
        response['Cache-Control'] = _CACHE_IMMUTABLE
        response['Accept-Ranges'] = 'bytes'
        return response

    # Fallback на django static serve (на випадок edge-кейсів).
    for root in roots:
        candidate = (root / safe).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            response = static_serve(request, path, document_root=str(root))
            response['Cache-Control'] = _CACHE_IMMUTABLE
            return response
    raise Http404('media')
