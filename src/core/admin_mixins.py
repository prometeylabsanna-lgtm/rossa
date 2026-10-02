from __future__ import annotations

import re

from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.admin_widgets import (
    CmsAdminColorWidget,
    CmsAdminImageWidget,
    CmsAdminTextInputWidget,
    CmsAdminTextareaWidget,
    tinymce_widget,
)
from core.models_styles import PageStyle
from core.page_styles import normalize_hex

_HEX_RE = re.compile(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$')

RICH_TEXT_FIELDS = {
    'body_uk', 'body_ru',
    'hero_sub_uk', 'hero_sub_ru',
    'about_body_uk', 'about_body_ru',
    'craft_body_uk', 'craft_body_ru',
    'intro_uk', 'intro_ru',
    'sub_uk', 'sub_ru',
    'description_uk', 'description_ru',
}


def clean_color(raw: str, *, default: str) -> str:
    value = (raw or '').strip()
    if not value:
        return ''
    if not _HEX_RE.match(value):
        raise forms.ValidationError('Вкажіть колір у форматі #986030')
    value = normalize_hex(value)
    if value == default.lower():
        return ''
    return value


class PageStyleFieldsMixin(forms.ModelForm):
    """Додає поля оформлення сторінки до форми контенту."""

    style_page_key: str = ''

    style_background = forms.CharField(required=False, label='Колір фону')
    style_text = forms.CharField(required=False, label='Колір тексту')
    style_accent = forms.CharField(required=False, label='Колір підсвітки')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style = PageStyle.for_page(self.style_page_key) if self.style_page_key else None
        specs = (
            ('style_background', PageStyle.DEFAULT_BACKGROUND, 'Колір фону', style.background_color if style else ''),
            ('style_text', PageStyle.DEFAULT_TEXT, 'Колір тексту', style.text_color if style else ''),
            ('style_accent', PageStyle.DEFAULT_ACCENT, 'Колір підсвітки', style.accent_color if style else ''),
        )
        for name, default, label, current in specs:
            field = self.fields[name]
            field.widget = CmsAdminColorWidget(default_color=default)
            field.label = label
            field.required = False
            field.initial = (current or '').strip() or default
            field.help_text = f'За замовчуванням: {default}. Якщо обрати цей колір — залишиться стиль сайту.'

    def clean_style_background(self):
        return clean_color(self.cleaned_data.get('style_background', ''), default=PageStyle.DEFAULT_BACKGROUND)

    def clean_style_text(self):
        return clean_color(self.cleaned_data.get('style_text', ''), default=PageStyle.DEFAULT_TEXT)

    def clean_style_accent(self):
        return clean_color(self.cleaned_data.get('style_accent', ''), default=PageStyle.DEFAULT_ACCENT)

    def save(self, commit=True):
        obj = super().save(commit=commit)
        if self.style_page_key:
            style = PageStyle.for_page(self.style_page_key)
            style.background_color = self.cleaned_data.get('style_background', '')
            style.text_color = self.cleaned_data.get('style_text', '')
            style.accent_color = self.cleaned_data.get('style_accent', '')
            style.save()
        return obj


class CmsWidgetsAdminMixin:
    """Превʼю фото + TinyMCE для довгих текстів + короткі поля як input."""

    change_form_template = 'admin/core/cms_change_form.html'

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, models.ImageField):
            kwargs['widget'] = CmsAdminImageWidget()
            return super().formfield_for_dbfield(db_field, request, **kwargs)

        if db_field.name in RICH_TEXT_FIELDS:
            kwargs['widget'] = tinymce_widget()
            return super().formfield_for_dbfield(db_field, request, **kwargs)

        if isinstance(db_field, (models.CharField, models.SlugField)) and not isinstance(db_field, models.TextField):
            kwargs.setdefault('widget', CmsAdminTextInputWidget())
        elif isinstance(db_field, models.TextField):
            kwargs.setdefault('widget', CmsAdminTextareaWidget(attrs={'rows': 4}))

        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def message_user(self, request, message, level=None, extra_tags='', fail_silently=False):
        text = str(message)
        if 'успішно' in text.lower() or 'was changed' in text.lower() or 'was added' in text.lower():
            message = _('Зміни успішно збережено!')
        return super().message_user(request, message, level=level, extra_tags=extra_tags, fail_silently=fail_silently)


class SingletonAdminMixin:
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


STYLE_TAB = {
    'classes': ('tab',),
    'fields': ('style_background', 'style_text', 'style_accent'),
}
