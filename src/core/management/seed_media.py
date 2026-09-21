from pathlib import Path

from django.core.files import File


STATIC_IMAGES = Path(__file__).resolve().parents[1] / 'static' / 'images'


def attach(field, relative: str, dest_name: str | None = None):
    src = STATIC_IMAGES / relative
    if not src.exists() or field:
        return
    name = dest_name or src.name
    with src.open('rb') as fh:
        field.save(name, File(fh), save=False)
