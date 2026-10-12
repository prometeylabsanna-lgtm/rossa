"""Кастомні поля моделей."""

from __future__ import annotations

from django.db.models.fields.files import ImageField, ImageFieldFile

from core.images_webp import convert_upload_to_webp, write_variants_for_bytes


class WebPImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        converted = convert_upload_to_webp(name, content)
        if converted is not None:
            name, content = converted
        result = super().save(name, content, save=save)
        try:
            self.open('rb')
            data = self.read()
            self.close()
            write_variants_for_bytes(self.storage, self.name, data)
        except Exception:
            # Variants — best-effort; головний файл уже збережено.
            pass
        return result


class WebPImageField(ImageField):
    """ImageField: оптимізація → WebP + responsive variants при збереженні."""

    attr_class = WebPImageFieldFile


    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        if cls._meta.abstract:
            return
        from django.db.models.signals import post_delete, pre_save

        from core import media_cleanup

        label = f'{cls._meta.app_label}.{cls.__name__}'
        pre_save.connect(media_cleanup.webp_pre_save, sender=cls, weak=False, dispatch_uid=f'webp_pre_save:{label}')
        post_delete.connect(media_cleanup.webp_post_delete, sender=cls, weak=False, dispatch_uid=f'webp_post_delete:{label}')
