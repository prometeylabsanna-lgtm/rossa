"""Оптимізація зображень: WebP + resize + responsive variants."""

from __future__ import annotations

import io
import re
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image

WEBP_QUALITY = 80
MAX_WIDTH = 1600
VARIANT_WIDTHS = (640, 960, 1600)
_SKIP_EXT = {'.gif'}
_IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff'}
_VARIANT_RE = re.compile(r'_w(\d+)$')


def needs_webp_convert(name: str | None) -> bool:
    ext = Path(name or '').suffix.lower()
    if not ext or ext in _SKIP_EXT:
        return False
    return ext != '.webp'


def _normalize_mode(img: Image.Image) -> Image.Image:
    if img.mode in ('RGBA', 'LA'):
        return img.convert('RGBA')
    if img.mode == 'P':
        return img.convert('RGBA' if 'transparency' in img.info else 'RGB')
    if img.mode != 'RGB':
        return img.convert('RGB')
    return img


def _resize_max(img: Image.Image, max_width: int) -> Image.Image:
    if max_width <= 0 or img.width <= max_width:
        return img
    ratio = max_width / float(img.width)
    height = max(1, int(round(img.height * ratio)))
    return img.resize((max_width, height), Image.Resampling.LANCZOS)


def encode_image_to_webp(
    img: Image.Image,
    *,
    quality: int = WEBP_QUALITY,
    max_width: int | None = MAX_WIDTH,
) -> bytes:
    prepared = _normalize_mode(img)
    if max_width is not None:
        prepared = _resize_max(prepared, max_width)
    buf = io.BytesIO()
    # method=4: баланс швидкість/розмір (method=6 надто повільний на 4K+).
    prepared.save(buf, format='WEBP', quality=quality, method=4)
    return buf.getvalue()


def convert_bytes_to_webp(
    data: bytes,
    *,
    source_name: str = '',
    quality: int = WEBP_QUALITY,
    max_width: int | None = MAX_WIDTH,
    force: bool = False,
) -> bytes | None:
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

    needs_resize = max_width is not None and img.width > max_width
    already_webp = fmt == 'WEBP' or Path(source_name).suffix.lower() == '.webp'
    if already_webp and not force and not needs_resize:
        return None

    return encode_image_to_webp(img, quality=quality, max_width=max_width)


def webp_filename(name: str) -> str:
    path = Path(name or 'image')
    if not path.suffix:
        return f'{path.name}.webp'
    return str(path.with_suffix('.webp'))


def base_stem(name: str) -> str:
    """Прибирає суфікс _wNNN зі stem (ontario_w640 → ontario)."""
    stem = Path(name or 'image').stem
    return _VARIANT_RE.sub('', stem)


def variant_storage_name(name: str, width: int) -> str:
    path = Path(name or 'image.webp')
    stem = base_stem(str(path))
    return str(path.with_name(f'{stem}_w{width}.webp'))


def variant_url(url: str, width: int) -> str:
    if not url:
        return ''
    path = Path(url)
    stem = base_stem(path.name)
    return str(path.with_name(f'{stem}_w{width}{path.suffix or ".webp"}'))


def srcset_from_url(url: str, widths: tuple[int, ...] = VARIANT_WIDTHS) -> str:
    if not url:
        return ''
    parts = [f'{variant_url(url, w)} {w}w' for w in widths]
    return ', '.join(parts)


def _read_upload(content) -> bytes:
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
    return data


def convert_upload_to_webp(name: str, content) -> tuple[str, ContentFile] | None:
    """
    Конвертує / оптимізує upload у WebP (max width).
    GIF пропускає. Вже-WebP теж ресайзить, якщо ширше за MAX_WIDTH.
    """
    source_name = name or getattr(content, 'name', '') or 'image'
    if Path(source_name).suffix.lower() in _SKIP_EXT:
        return None

    data = _read_upload(content)
    force = Path(source_name).suffix.lower() == '.webp'
    webp_data = convert_bytes_to_webp(
        data,
        source_name=source_name,
        force=force,
    )
    if webp_data is None:
        return None

    new_name = webp_filename(source_name)
    # Прибираємо попередній _wNNN зі імені поля — головний файл без суфікса.
    path = Path(new_name)
    clean = path.with_name(f'{base_stem(str(path))}.webp')
    return str(clean), ContentFile(webp_data, name=clean.name)


def write_variants_for_bytes(
    storage,
    name: str,
    data: bytes,
    *,
    widths: tuple[int, ...] = VARIANT_WIDTHS,
    quality: int = WEBP_QUALITY,
) -> list[str]:
    """Пише responsive variants поруч із головним файлом. Повертає список імен."""
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:
        return []

    written: list[str] = []
    for width in widths:
        if img.width < width and width != max(widths):
            # Не апскейлимо; для найменших все одно пишемо максимум наявної ширини.
            if img.width < min(widths):
                continue
        variant_bytes = encode_image_to_webp(img, quality=quality, max_width=width)
        vname = variant_storage_name(name, width)
        if storage.exists(vname):
            storage.delete(vname)
        storage.save(vname, ContentFile(variant_bytes, name=Path(vname).name))
        written.append(vname)
    return written


def optimize_file_bytes(
    data: bytes,
    *,
    source_name: str = '',
    quality: int = WEBP_QUALITY,
    max_width: int = MAX_WIDTH,
) -> bytes | None:
    """Примусова оптимізація (для management command / існуючих webp)."""
    return convert_bytes_to_webp(
        data,
        source_name=source_name,
        quality=quality,
        max_width=max_width,
        force=True,
    )


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
    if ext in _SKIP_EXT:
        return False
    return ext in _IMAGE_EXT or needs_webp_convert(name)


def is_optimizable_media_name(name: str | None) -> bool:
    if not name:
        return False
    ext = Path(name).suffix.lower()
    if ext in _SKIP_EXT:
        return False
    return ext in _IMAGE_EXT
