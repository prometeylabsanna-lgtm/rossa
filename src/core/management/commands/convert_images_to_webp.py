"""Міграція існуючих медіа ImageField та JSON-галерей у WebP."""

from __future__ import annotations

from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db import models

from core.images_webp import (
    convert_bytes_to_webp,
    is_convertible_media_name,
    media_storage_name,
    webp_filename,
)

JSON_IMAGE_FIELDS = (
    ('core', 'AboutPage', 'craft_images'),
    ('core', 'AboutPage', 'logo_images'),
    ('core', 'AboutPage', 'evolution_images'),
)


class Command(BaseCommand):
    help = 'Конвертує існуючі jpg/png зображення в WebP (GIF пропускає).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Лише показати, що буде змінено, без запису.',
        )

    def handle(self, *args, **options):
        dry = options['dry_run']
        converted = 0
        skipped = 0
        errors = 0

        field_stats = self._convert_image_fields(dry)
        converted += field_stats[0]
        skipped += field_stats[1]
        errors += field_stats[2]

        json_stats = self._convert_json_galleries(dry)
        converted += json_stats[0]
        skipped += json_stats[1]
        errors += json_stats[2]

        prefix = '[dry-run] ' if dry else ''
        self.stdout.write(
            self.style.SUCCESS(
                f'{prefix}Готово: конвертовано={converted}, пропущено={skipped}, помилки={errors}'
            )
        )

    def _convert_image_fields(self, dry: bool) -> tuple[int, int, int]:
        converted = skipped = errors = 0
        for model in apps.get_models():
            if model._meta.proxy:
                continue
            image_fields = [
                f for f in model._meta.concrete_fields
                if isinstance(f, models.ImageField)
            ]
            if not image_fields:
                continue

            for obj in model.objects.all().iterator():
                update_fields: list[str] = []
                for field in image_fields:
                    file_field = getattr(obj, field.name)
                    if not file_field or not file_field.name:
                        continue
                    if not is_convertible_media_name(file_field.name):
                        skipped += 1
                        continue

                    old_name = file_field.name
                    try:
                        with file_field.open('rb') as fh:
                            data = fh.read()
                        webp_data = convert_bytes_to_webp(data, source_name=old_name)
                        if webp_data is None:
                            skipped += 1
                            continue
                        new_name = webp_filename(old_name)
                        self.stdout.write(f'{model._meta.label}.{field.name}: {old_name} → {new_name}')
                        if not dry:
                            saved = default_storage.save(
                                new_name,
                                ContentFile(webp_data, name=Path(new_name).name),
                            )
                            setattr(obj, field.name, saved)
                            if old_name != saved and default_storage.exists(old_name):
                                default_storage.delete(old_name)
                            update_fields.append(field.name)
                        converted += 1
                    except Exception as exc:
                        errors += 1
                        self.stderr.write(
                            f'Помилка {model._meta.label}.{field.name} ({old_name}): {exc}'
                        )

                if update_fields and not dry:
                    obj.save(update_fields=list(dict.fromkeys(update_fields)))

        return converted, skipped, errors

    def _convert_json_galleries(self, dry: bool) -> tuple[int, int, int]:
        converted = skipped = errors = 0
        media_url = settings.MEDIA_URL or '/media/'

        for app_label, model_name, field_name in JSON_IMAGE_FIELDS:
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                continue

            for obj in model.objects.all().iterator():
                items = getattr(obj, field_name, None)
                if not isinstance(items, list) or not items:
                    continue

                changed = False
                new_items = []
                for item in items:
                    if not isinstance(item, dict):
                        new_items.append(item)
                        continue
                    row = dict(item)
                    ref = row.get('image')
                    storage_name = media_storage_name(str(ref or ''))
                    if not storage_name or not is_convertible_media_name(storage_name):
                        if storage_name:
                            skipped += 1
                        new_items.append(row)
                        continue

                    try:
                        if not default_storage.exists(storage_name):
                            skipped += 1
                            new_items.append(row)
                            continue
                        with default_storage.open(storage_name, 'rb') as fh:
                            data = fh.read()
                        webp_data = convert_bytes_to_webp(data, source_name=storage_name)
                        if webp_data is None:
                            skipped += 1
                            new_items.append(row)
                            continue

                        new_name = webp_filename(storage_name)
                        self.stdout.write(
                            f'{model._meta.label}.{field_name}: {storage_name} → {new_name}'
                        )
                        if not dry:
                            saved = default_storage.save(
                                new_name,
                                ContentFile(webp_data, name=Path(new_name).name),
                            )
                            if storage_name != saved and default_storage.exists(storage_name):
                                default_storage.delete(storage_name)
                            row['image'] = f'{media_url}{saved}'
                            changed = True
                        converted += 1
                    except Exception as exc:
                        errors += 1
                        self.stderr.write(
                            f'Помилка {model._meta.label}.{field_name} ({storage_name}): {exc}'
                        )
                    new_items.append(row)

                if changed and not dry:
                    setattr(obj, field_name, new_items)
                    obj.save(update_fields=[field_name])

        return converted, skipped, errors
