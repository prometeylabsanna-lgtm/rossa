"""Оптимізує існуючі медіа: WebP, resize, responsive variants."""

from __future__ import annotations

import io
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image

from core.images_webp import (
    MAX_WIDTH,
    VARIANT_WIDTHS,
    WEBP_QUALITY,
    base_stem,
    encode_image_to_webp,
    is_optimizable_media_name,
    optimize_file_bytes,
    variant_storage_name,
)

_VARIANT_STEM = re.compile(r'.*_w\d+$')


class Command(BaseCommand):
    help = 'Оптимізує jpg/png/webp у MEDIA_ROOT / media_demo: resize + variants.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--root', default='')
        parser.add_argument('--max-width', type=int, default=MAX_WIDTH)
        parser.add_argument('--quality', type=int, default=WEBP_QUALITY)

    def handle(self, *args, **options):
        dry = options['dry_run']
        max_width = options['max_width']
        quality = options['quality']
        root = Path(options['root'] or settings.MEDIA_ROOT)
        if not root.is_dir():
            self.stderr.write(f'Немає директорії: {root}')
            return

        changed = 0
        skipped = 0
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.name.startswith('.'):
                continue
            if _VARIANT_STEM.match(path.stem):
                continue
            # Не чіпаємо фавікони / дрібну UI-графіку.
            if 'favicon' in path.parts:
                skipped += 1
                continue
            if not is_optimizable_media_name(path.name):
                skipped += 1
                continue
            if path.suffix.lower() in {'.ico'}:
                skipped += 1
                continue

            rel = path.relative_to(root).as_posix()
            try:
                img = Image.open(path)
                img.load()
            except Exception as exc:
                self.stderr.write(f'SKIP {rel}: {exc}')
                skipped += 1
                continue

            out_rel = rel if path.suffix.lower() == '.webp' else str(Path(rel).with_suffix('.webp'))
            out_rel = str(Path(out_rel).with_name(f'{base_stem(out_rel)}.webp'))
            needs_main = (
                path.suffix.lower() != '.webp'
                or img.width > max_width
                or path.stat().st_size > 180_000
            )

            if dry:
                self.stdout.write(
                    f'{"OPT" if needs_main else "VAR"} {rel} {img.size[0]}x{img.size[1]} '
                    f'{path.stat().st_size}B → {out_rel}'
                )
                changed += 1
                continue

            data = path.read_bytes()
            if needs_main:
                optimized = optimize_file_bytes(
                    data,
                    source_name=path.name,
                    quality=quality,
                    max_width=max_width,
                )
                if optimized is None:
                    optimized = encode_image_to_webp(img, quality=quality, max_width=max_width)
                out_path = root / out_rel
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(optimized)
                if out_path.resolve() != path.resolve():
                    path.unlink(missing_ok=True)
                data = optimized
            else:
                out_path = root / out_rel
                if out_path.resolve() != path.resolve():
                    out_path.write_bytes(data)
                    path.unlink(missing_ok=True)
                data = out_path.read_bytes()

            self._write_disk_variants(root, out_rel, data, quality=quality)
            changed += 1
            self.stdout.write(self.style.SUCCESS(f'OK {out_rel}'))

        self.stdout.write(f'Done: {changed} processed, {skipped} skipped, dry_run={dry}')

    def _write_disk_variants(self, root: Path, rel: str, data: bytes, *, quality: int) -> None:
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
        except Exception:
            return
        for width in VARIANT_WIDTHS:
            vrel = variant_storage_name(rel, width)
            vbytes = encode_image_to_webp(img, quality=quality, max_width=width)
            vpath = root / vrel
            vpath.parent.mkdir(parents=True, exist_ok=True)
            vpath.write_bytes(vbytes)
