from pathlib import Path

from django.core.files import File
from django.core.files.storage import default_storage


STATIC_IMAGES = Path(__file__).resolve().parents[1] / 'static' / 'images'
SLOTS_DIR = STATIC_IMAGES / 'slots'

# Craft-мозаїка «Про нас» — основний файл + responsive variants у slots/.
ABOUT_CRAFT_FILES = (
    'about-fabric.webp',
    'about-frame.webp',
    'about-assembly.webp',
)


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


def _save_storage_file(dest: str, src: Path, *, force: bool = False) -> bool:
    """Копіює файл у default_storage під канонічним імʼям. Повертає True якщо записано."""
    if not src.is_file():
        return False
    if not force:
        try:
            if default_storage.exists(dest):
                return False
        except Exception:
            pass
    _delete_if_exists(default_storage, dest)
    with src.open('rb') as fh:
        default_storage.save(dest, File(fh))
    return True


def sync_slot_file(filename: str, dest_dir: str = 'about', *, force: bool = False) -> list[str]:
    """Копіює slot + усі `_wNNN.webp` variants у MEDIA (для Docker volume)."""
    written: list[str] = []
    src = SLOTS_DIR / filename
    dest = f'{dest_dir.rstrip("/")}/{filename}'
    if _save_storage_file(dest, src, force=force):
        written.append(dest)
    stem = Path(filename).stem
    for variant in sorted(SLOTS_DIR.glob(f'{stem}_w*.webp')):
        vdest = f'{dest_dir.rstrip("/")}/{variant.name}'
        if _save_storage_file(vdest, variant, force=force):
            written.append(vdest)
    return written


def ensure_about_craft_media(*, force: bool = False) -> list[str]:
    """Гарантує наявність craft-фото «Про нас» у MEDIA_ROOT / volume."""
    written: list[str] = []
    for filename in ABOUT_CRAFT_FILES:
        written.extend(sync_slot_file(filename, 'about', force=force))
    return written
