"""Конвертація завантажених зображень у WebP (без ресайзу)."""

from __future__ import annotations

import io
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image

WEBP_QUALITY = 95
_SKIP_EXT = {'.gif'}
_WEBP_EXT = {'.webp'}
_IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff'}


def needs_webp_convert(name: str | None) -> bool:
    ext = Path(name or '').suffix.lower()
    if not ext or ext in _SKIP_EXT or ext in _WEBP_EXT:
        return False
    return True


def _normalize_mode(img: Image.Image) -> Image.Image:
    if img.mode in ('RGBA', 'LA'):
        return img.convert('RGBA')
    if img.mode == 'P':
        return img.convert('RGBA' if 'transparency' in img.info else 'RGB')
    if img.mode != 'RGB':
        return img.convert('RGB')
    return img


def encode_image_to_webp(img: Image.Image) -> bytes:
    prepared = _normalize_mode(img)
    buf = io.BytesIO()
    prepared.save(buf, format='WEBP', quality=WEBP_QUALITY, method=6)
    return buf.getvalue()


def convert_bytes_to_webp(data: bytes, *, source_name: str = '') -> bytes | None:
    """Повертає WebP-байти або None, якщо конвертація не потрібна / неможлива."""
    if not data:
        return None
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:
        return None

    fmt = (img.format or '').upper()
    if fmt == 'GIF' or Path(source_name).suffix.lower() in _SKIP_EXT:
        return None
    if fmt == 'WEBP' and not needs_webp_convert(source_name):
        return None

    return encode_image_to_webp(img)


def webp_filename(name: str) -> str:
    path = Path(name or 'image')
    if not path.suffix:
        return f'{path.name}.webp'
    return str(path.with_suffix('.webp'))


def convert_upload_to_webp(name: str, content) -> tuple[str, ContentFile] | None:
    """
    Конвертує upload у WebP.
    Повертає (нове_імʼя, ContentFile) або None (залишити як є).
    """
    source_name = name or getattr(content, 'name', '') or 'image'
    if Path(source_name).suffix.lower() in _SKIP_EXT | _WEBP_EXT:
        return None

    if hasattr(content, 'open'):
        try:
            content.open('rb')
        except Exception:
            pass
    if hasattr(content, 'seek'):
        try:
            content.seek(0)
        except Exception:
            pass

    data = content.read() if hasattr(content, 'read') else bytes(content)
    if hasattr(content, 'seek'):
        try:
            content.seek(0)
        except Exception:
            pass

    webp_data = convert_bytes_to_webp(data, source_name=source_name)
    if webp_data is None:
        return None

    new_name = webp_filename(source_name)
    return new_name, ContentFile(webp_data, name=Path(new_name).name)


def media_storage_name(ref: str) -> str | None:
    """Витягує шлях у storage з /media/... або повного URL."""
    value = (ref or '').strip()
    if not value:
        return None
    media_url = settings.MEDIA_URL or '/media/'
    if value.startswith(media_url):
        return value[len(media_url):].lstrip('/')
    marker = media_url if media_url.startswith('/') else f'/{media_url}'
    idx = value.find(marker)
    if idx >= 0:
        return value[idx + len(marker):].lstrip('/')
    if '://' not in value and not value.startswith('/'):
        return value.lstrip('/')
    return None


def is_convertible_media_name(name: str | None) -> bool:
    if not name:
        return False
    ext = Path(name).suffix.lower()
    if ext in _SKIP_EXT or ext in _WEBP_EXT:
        return False
    return ext in _IMAGE_EXT or needs_webp_convert(name)
