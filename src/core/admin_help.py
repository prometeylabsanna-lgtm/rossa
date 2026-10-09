"""Короткі підказки лімітів для полів адмінки (без технічних деталей)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.fields.files import FieldFile

from core.cms_text import cms_html_to_plain

IMAGE_MAX_MB = 8
IMAGE_MAX_BYTES = IMAGE_MAX_MB * 1024 * 1024

# JSON-галереї з фото
_JSON_IMAGE_FIELDS = frozenset({
    'evolution_images',
    'craft_images',
    'logo_images',
})

# Поля, де ліміт символів лише заважає (колір, службові коди)
_SKIP_CHAR_HINT = frozenset({
    'hex_color',
    'badge',
    'status',
    'language',
    'collab_type',
    'fulfillment',
})


def hint_chars(limit: int) -> str:
    return f'Не більше {limit} символів.'


def hint_image_mb(mb: int = IMAGE_MAX_MB) -> str:
    return f'Не більше {mb} МБ.'


def text_char_limit(model: type[models.Model] | None, field_name: str) -> int | None:
    """Мʼякі ліміти для TextField, щоб не ламалась верстка блоків."""
    name = field_name
    model_name = model.__name__ if model is not None else ''

    if name.startswith('seo_description'):
        return 160
    if name.startswith('craft_body'):
        return 220
    if name.startswith('about_body'):
        return 280
    if name.startswith('description'):
        return 500
    if name.startswith('care_'):
        return 200
    if name in ('comment', 'message'):
        return 1000
    if name in ('body_uk', 'body_ru'):
        if model_name == 'ValueProp':
            return 150
        if model_name == 'AboutPage':
            return 2000
        if model_name in {'LegalPage', 'DeliveryPage', 'OfferPage', 'PrivacyPage'}:
            return 5000
        return 2000
    return 3000


def _plain_len(value: str) -> int:
    return len(cms_html_to_plain(value or ''))


def validate_plain_text_max_length(limit: int):
    def _validator(value):
        if value in (None, ''):
            return
        if _plain_len(str(value)) > limit:
            raise ValidationError(hint_chars(limit))

    _validator.__name__ = f'plain_text_max_{limit}'
    return _validator


def validate_image_max_size(value):
    if not value:
        return
    size = getattr(value, 'size', None)
    if size is None and isinstance(value, FieldFile):
        try:
            size = value.size
        except Exception:
            size = None
    if size is not None and size > IMAGE_MAX_BYTES:
        raise ValidationError(hint_image_mb())


def _merge_help(existing, hint: str) -> str:
    base = str(existing or '').strip()
    if not hint:
        return base
    if hint in base:
        return base
    if not base:
        return hint
    return f'{base} {hint}'


def _has_choices(db_field: models.Field) -> bool:
    choices = getattr(db_field, 'choices', None)
    return bool(choices)


def apply_admin_field_hints(
    db_field: models.Field,
    formfield,
    *,
    model: type[models.Model] | None = None,
):
    """Додає help_text і валідатори лімітів до поля форми адмінки."""
    if formfield is None:
        return formfield

    name = db_field.name

    if isinstance(db_field, models.ImageField):
        formfield.help_text = _merge_help(formfield.help_text, hint_image_mb())
        validators = list(formfield.validators or [])
        if validate_image_max_size not in validators:
            validators.append(validate_image_max_size)
        formfield.validators = validators
        return formfield

    if isinstance(db_field, models.JSONField) and name in _JSON_IMAGE_FIELDS:
        formfield.help_text = _merge_help(
            formfield.help_text,
            f'Кожне фото — не більше {IMAGE_MAX_MB} МБ.',
        )
        return formfield

    if isinstance(db_field, models.TextField):
        limit = text_char_limit(model, name)
        if limit:
            formfield.help_text = _merge_help(formfield.help_text, hint_chars(limit))
            validators = list(formfield.validators or [])
            validators.append(validate_plain_text_max_length(limit))
            formfield.validators = validators
            # TinyMCE ігнорує maxlength — ліміт лише через валідатор + підказку
            widget_name = formfield.widget.__class__.__name__.lower()
            if 'tinymce' not in widget_name and hasattr(formfield.widget, 'attrs'):
                formfield.widget.attrs.setdefault('maxlength', str(limit))
        return formfield

    if isinstance(db_field, (models.CharField, models.SlugField)):
        if name in _SKIP_CHAR_HINT or _has_choices(db_field):
            return formfield
        limit = getattr(db_field, 'max_length', None)
        if limit:
            formfield.help_text = _merge_help(formfield.help_text, hint_chars(limit))
        return formfield

    return formfield
