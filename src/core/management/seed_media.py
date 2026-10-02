from pathlib import Path

from django.core.files import File


STATIC_IMAGES = Path(__file__).resolve().parents[1] / 'static' / 'images'


def _storage_has(field) -> bool:
    if not field or not field.name:
        return False
    try:
        return field.storage.exists(field.name)
    except Exception:
        return False


def attach(field, relative: str, dest_name: str | None = None):
    """Записати файл, якщо поля порожнє АБО файл відсутній на диску (Vercel seed)."""
    src = STATIC_IMAGES / relative
    if not src.exists():
        return
    if _storage_has(field):
        return
    # Зберігаємо імʼя з БД (щоб не плодити milan_XXXX.webp), інакше — з сорсу.
    if field and field.name:
        name = Path(field.name).name
    else:
        name = dest_name or src.name
    with src.open('rb') as fh:
        field.save(name, File(fh), save=False)


def replace_file(field, relative: str, dest_name: str | None = None):
    src = STATIC_IMAGES / relative
    if not src.exists():
        return
    if field and field.name:
        name = Path(field.name).name
    else:
        name = dest_name or src.name
    with src.open('rb') as fh:
        field.save(name, File(fh), save=False)
