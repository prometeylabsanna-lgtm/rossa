from pathlib import Path

from django.core.files import File


STATIC_IMAGES = Path(__file__).resolve().parents[1] / 'static' / 'images'


def _canonical_name(field, relative: str, dest_name: str | None = None) -> str:
    src = STATIC_IMAGES / relative
    return dest_name or src.name


def _target_path(field, name: str) -> str:
    return field.field.generate_filename(field.instance, name)


def _delete_if_exists(storage, name: str) -> None:
    if not name:
        return
    try:
        if storage.exists(name):
            storage.delete(name)
    except Exception:
        pass


def _write(field, relative: str, dest_name: str | None = None) -> None:
    """Записати файл під канонічним імʼям (без milan_XXXX), з overwrite."""
    src = STATIC_IMAGES / relative
    if not src.exists():
        return
    name = _canonical_name(field, relative, dest_name)
    target = _target_path(field, name)
    # Прибрати старий хешований шлях і ціль — інакше Django додасть суфікс.
    if field.name and field.name != target:
        _delete_if_exists(field.storage, field.name)
    _delete_if_exists(field.storage, target)
    with src.open('rb') as fh:
        field.save(name, File(fh), save=False)


def attach(field, relative: str, dest_name: str | None = None):
    """Записати файл, якщо поля порожнє АБО канонічний файл відсутній (Vercel seed)."""
    src = STATIC_IMAGES / relative
    if not src.exists():
        return
    name = _canonical_name(field, relative, dest_name)
    target = _target_path(field, name)
    try:
        if field.name == target and field.storage.exists(target):
            return
    except Exception:
        pass
    _write(field, relative, dest_name)


def replace_file(field, relative: str, dest_name: str | None = None):
    _write(field, relative, dest_name)
