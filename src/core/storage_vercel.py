"""Медіа-сховище для Vercel: запис у /tmp, читання з /tmp або з media_demo."""
from __future__ import annotations

from pathlib import Path

from django.core.files.storage import FileSystemStorage


class VercelMediaStorage(FileSystemStorage):
    """
    Runtime на Vercel: пакет read-only.
    Нові файли (адмінка) пишемо в location (/tmp/media),
    існуючі демо-файли читаємо з packaged_root (media_demo).
    """

    def __init__(self, *args, packaged_root: str | Path | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.packaged_root = Path(packaged_root) if packaged_root else None

    def _writable_path(self, name: str) -> Path:
        return Path(self.path(name))

    def _packaged_file(self, name: str) -> Path | None:
        if not self.packaged_root:
            return None
        candidate = (self.packaged_root / name).resolve()
        root = self.packaged_root.resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return None
        return candidate if candidate.is_file() else None

    def exists(self, name: str) -> bool:
        if super().exists(name):
            return True
        return self._packaged_file(name) is not None

    def _open(self, name: str, mode: str = 'rb'):
        if 'b' not in mode:
            mode += 'b'
        if any(flag in mode for flag in ('w', 'a', 'x', '+')):
            self._writable_path(name).parent.mkdir(parents=True, exist_ok=True)
            return super()._open(name, mode)
        if super().exists(name):
            return super()._open(name, mode)
        packaged = self._packaged_file(name)
        if packaged is not None:
            return packaged.open(mode)
        return super()._open(name, mode)

    def delete(self, name: str) -> None:
        if super().exists(name):
            super().delete(name)

    def size(self, name: str) -> int:
        if super().exists(name):
            return super().size(name)
        packaged = self._packaged_file(name)
        if packaged is not None:
            return packaged.stat().st_size
        return super().size(name)

    def get_modified_time(self, name: str):
        if super().exists(name):
            return super().get_modified_time(name)
        packaged = self._packaged_file(name)
        if packaged is not None:
            from datetime import datetime, timezone

            return datetime.fromtimestamp(packaged.stat().st_mtime, tz=timezone.utc)
        return super().get_modified_time(name)
