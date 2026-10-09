"""Кастомні поля моделей."""

from __future__ import annotations

from django.db.models.fields.files import ImageField, ImageFieldFile

from core.images_webp import convert_upload_to_webp


class WebPImageFieldFile(ImageFieldFile):
    def save(self, name, content, save=True):
        converted = convert_upload_to_webp(name, content)
        if converted is not None:
            name, content = converted
        return super().save(name, content, save=save)


class WebPImageField(ImageField):
    """ImageField: jpg/png тощо → WebP при збереженні; GIF без змін."""

    attr_class = WebPImageFieldFile
