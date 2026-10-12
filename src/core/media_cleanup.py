"""Прибирання осиротілих медіафайлів (головний файл + _wNNN variants).

Видаляємо лише після успішного commit (transaction.on_commit) і лише якщо
файл більше ніде не використовується: ні в WebPImageField жодної моделі,
ні в JSON-галереях AboutPage (craft/logo/evolution_images).

Обмеження (bug 3): файл, завантажений через /cms-upload/, але так і не
збережений у формі (адмін закрив сторінку без «Зберегти»), не відстежується —
це неможливо надійно визначити на сервері. Такі файли лишаються в about/*.
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from django.apps import apps
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction

from core.images_webp import VARIANT_WIDTHS, variant_storage_name

log = logging.getLogger(__name__)

GALLERY_FIELDS = ('craft_images', 'logo_images', 'evolution_images')
GALLERY_PREFIXES = ('about/',)


def variant_names(name: str) -> list[str]:
    return [name, *(variant_storage_name(name, w) for w in VARIANT_WIDTHS)]


def delete_with_variants(storage, name: str) -> list[str]:
    deleted = []
    if not name:
        return deleted
    for vname in variant_names(name):
        try:
            if storage.exists(vname):
                storage.delete(vname)
                deleted.append(vname)
        except Exception:  # pragma: no cover - best effort
            log.warning('media cleanup: failed to delete %s', vname, exc_info=True)
    return deleted


def _webp_fields():
    from core.fields import WebPImageField
    for model in apps.get_models():
        for f in model._meta.concrete_fields:
            if isinstance(f, WebPImageField):
                yield model, f


def url_to_name(url: str) -> str:
    if not url:
        return ''
    path = urlparse(str(url)).path
    media = settings.MEDIA_URL or '/media/'
    if path.startswith(media):
        return path[len(media):]
    return ''


def gallery_names(instance) -> set[str]:
    names = set()
    for field in GALLERY_FIELDS:
        for item in getattr(instance, field, None) or []:
            if isinstance(item, dict):
                name = url_to_name(item.get('image', ''))
                if name.startswith(GALLERY_PREFIXES):
                    names.add(name)
    return names


def is_referenced(name: str) -> bool:
    if not name:
        return True
    for model, f in _webp_fields():
        if model._default_manager.filter(**{f.name: name}).exists():
            return True
    AboutPage = apps.get_model('core', 'AboutPage')
    for page in AboutPage.objects.all():
        if name in gallery_names(page):
            return True
    return False


def schedule_cleanup(names, storage=None) -> None:
    storage = storage or default_storage
    names = {n for n in names if n}
    if not names:
        return

    def _run():
        for n in names:
            if not is_referenced(n):
                delete_with_variants(storage, n)

    transaction.on_commit(_run)


# --- signal handlers ---------------------------------------------------------

def _webp_names(instance) -> dict:
    from core.fields import WebPImageField
    out = {}
    for f in instance._meta.concrete_fields:
        if isinstance(f, WebPImageField):
            ff = getattr(instance, f.attname)
            out[f.attname] = (ff.name if ff else '', ff.storage)
    return out


def webp_pre_save(sender, instance, raw=False, **kwargs):
    if raw or instance._state.adding or not instance.pk:
        return
    try:
        old = sender._default_manager.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    new = _webp_names(instance)
    for attname, (old_name, storage) in _webp_names(old).items():
        if old_name and old_name != new.get(attname, ('',))[0]:
            schedule_cleanup([old_name], storage)


def webp_post_delete(sender, instance, **kwargs):
    for name, storage in _webp_names(instance).values():
        schedule_cleanup([name], storage)


def gallery_pre_save(sender, instance, raw=False, **kwargs):
    if raw or not instance.pk:
        return
    try:
        old = sender._default_manager.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    removed = gallery_names(old) - gallery_names(instance)
    schedule_cleanup(removed)


def gallery_post_delete(sender, instance, **kwargs):
    schedule_cleanup(gallery_names(instance))
