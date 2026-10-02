"""Роздача /media/ з кількох коренів (Vercel: /tmp + media_demo)."""
from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.views.static import serve as static_serve


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
        if candidate.is_file():
            return static_serve(request, path, document_root=str(root))
    raise Http404('media')
