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
