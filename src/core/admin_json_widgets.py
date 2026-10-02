"""Віджети JSON-списків для CMS (галереї / віхи)."""

from __future__ import annotations

import json
from typing import Any

from django.forms.widgets import Widget

from core.cms_text import cms_html_to_plain, ensure_cms_html


SCHEMA_EVOLUTION = {
    'kind': 'evolution',
    'upload_to': 'about/evolution/',
    'add_label': 'Додати фото',
    'fields': (
        {'key': 'image', 'type': 'image', 'label': 'Фото', 'required': True},
    ),
}

SCHEMA_CRAFT = {
    'kind': 'craft',
    'upload_to': 'about/',
    'add_label': 'Додати фото',
    'fields': (
        {'key': 'image', 'type': 'image', 'label': 'Фото', 'required': True},
        {'key': 'label_uk', 'type': 'text', 'label': 'Підпис (ukr)'},
        {'key': 'label_ru', 'type': 'text', 'label': 'Підпис (ru)'},
    ),
}

SCHEMA_LOGO = {
    'kind': 'logo',
    'upload_to': 'about/logos/',
    'add_label': 'Додати логотип',
    'fields': (
        {'key': 'image', 'type': 'image', 'label': 'Фото', 'required': True},
        {'key': 'year', 'type': 'text', 'label': 'Рік'},
        {'key': 'label_uk', 'type': 'text', 'label': 'Підпис (ukr)'},
        {'key': 'label_ru', 'type': 'text', 'label': 'Підпис (ru)'},
    ),
}

SCHEMA_MILESTONES = {
    'kind': 'milestones',
    'upload_to': '',
    'add_label': 'Додати віху',
    'fields': (
        {'key': 'year', 'type': 'text', 'label': 'Рік', 'required': True},
        {'key': 'body_uk', 'type': 'textarea', 'label': 'Текст (ukr)', 'html': True},
        {'key': 'body_ru', 'type': 'textarea', 'label': 'Текст (ru)', 'html': True},
    ),
}

BENEFIT_ICON_CHOICES = (
    {'value': 'years', 'label': '20+ років'},
    {'value': 'production', 'label': 'Виробництво'},
    {'value': 'guarantee', 'label': 'Гарантія'},
    {'value': 'collections', 'label': 'Колекції'},
    {'value': 'design', 'label': 'Дизайн'},
)

SCHEMA_BENEFITS = {
    'kind': 'benefits',
    'upload_to': '',
    'add_label': 'Додати перевагу',
    'fields': (
        {
            'key': 'icon',
            'type': 'select',
            'label': 'Іконка',
            'required': True,
            'choices': BENEFIT_ICON_CHOICES,
        },
        {'key': 'title_uk', 'type': 'text', 'label': 'Заголовок (ukr)', 'required': True},
        {'key': 'title_ru', 'type': 'text', 'label': 'Заголовок (ru)'},
    ),
}

SCHEMA_DEALER_SUPPORT = {
    'kind': 'dealer_support',
    'upload_to': '',
    'add_label': 'Додати пункт підтримки',
    'fields': (
        {'key': 'title_uk', 'type': 'text', 'label': 'Заголовок (ukr)', 'required': True},
        {'key': 'title_ru', 'type': 'text', 'label': 'Заголовок (ru)'},
        {'key': 'body_uk', 'type': 'textarea', 'label': 'Текст (ukr)', 'html': True},
        {'key': 'body_ru', 'type': 'textarea', 'label': 'Текст (ru)', 'html': True},
    ),
}

JSON_LIST_SCHEMAS = {
    'evolution_images': SCHEMA_EVOLUTION,
    'craft_images': SCHEMA_CRAFT,
    'logo_images': SCHEMA_LOGO,
    'milestones': SCHEMA_MILESTONES,
    'benefits': SCHEMA_BENEFITS,
    'dealer_support': SCHEMA_DEALER_SUPPORT,
}


def _html_field_keys(schema: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        str(field['key'])
        for field in schema.get('fields') or ()
        if isinstance(field, dict) and field.get('html')
    )


def _items_for_admin(items: Any, html_keys: tuple[str, ...]) -> list:
    if not isinstance(items, list):
        return []
    out = []
    for item in items:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        for key in html_keys:
            if key in row and row[key]:
                row[key] = cms_html_to_plain(str(row[key]))
        out.append(row)
    return out


def _items_for_storage(items: list, html_keys: tuple[str, ...]) -> list:
    cleaned = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if all(str(v or '').strip() == '' for v in item.values()):
            continue
        row = dict(item)
        for key in html_keys:
            if key in row:
                row[key] = ensure_cms_html(str(row.get(key) or ''))
        cleaned.append(row)
    return cleaned


class CmsJsonListWidget(Widget):
    template_name = 'django/forms/widgets/cms_json_list.html'

    class Media:
        css = {'all': ('css/admin/cms_json_list.css',)}
        js = ('js/admin/cms_json_list.js',)

    def __init__(self, schema: dict[str, Any], attrs: dict[str, Any] | None = None) -> None:
        self.schema = schema
        self.html_keys = _html_field_keys(schema)
        super().__init__(attrs)

    def _parse_list(self, value) -> list:
        if value in (None, ''):
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value.strip() or '[]')
            except (TypeError, ValueError, json.JSONDecodeError):
                return []
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return [parsed]
        return []

    def format_value(self, value):
        items = _items_for_admin(self._parse_list(value), self.html_keys)
        return json.dumps(items, ensure_ascii=False)

    def value_from_datadict(self, data, files, name):
        raw = data.get(name, '[]')
        items = self._parse_list(raw)
        return _items_for_storage(items, self.html_keys)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        formatted = self.format_value(value)
        context['widget']['value'] = formatted
        context['widget']['schema_json'] = json.dumps(self.schema, ensure_ascii=False)
        context['widget']['items_json'] = formatted
        context['widget']['add_label'] = self.schema.get('add_label', 'Додати')
        context['widget']['kind'] = self.schema.get('kind', 'list')
        context['widget']['upload_to'] = self.schema.get('upload_to', '')
        return context


def cms_json_list_widget(field_name: str) -> CmsJsonListWidget | None:
    schema = JSON_LIST_SCHEMAS.get(field_name)
    if not schema:
        return None
    return CmsJsonListWidget(schema=schema)
