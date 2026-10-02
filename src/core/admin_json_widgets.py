"""Віджети JSON-списків для CMS (галереї / віхи)."""

from __future__ import annotations

import json
from typing import Any

from django.forms.widgets import Widget


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
        {'key': 'label_uk', 'type': 'text', 'label': 'Підпис (укр)'},
        {'key': 'label_ru', 'type': 'text', 'label': 'Підпис (рос)'},
    ),
}

SCHEMA_LOGO = {
    'kind': 'logo',
    'upload_to': 'about/logos/',
    'add_label': 'Додати логотип',
    'fields': (
        {'key': 'image', 'type': 'image', 'label': 'Фото', 'required': True},
        {'key': 'year', 'type': 'text', 'label': 'Рік'},
        {'key': 'label_uk', 'type': 'text', 'label': 'Підпис (укр)'},
        {'key': 'label_ru', 'type': 'text', 'label': 'Підпис (рос)'},
    ),
}

SCHEMA_MILESTONES = {
    'kind': 'milestones',
    'upload_to': '',
    'add_label': 'Додати віху',
    'fields': (
        {'key': 'year', 'type': 'text', 'label': 'Рік', 'required': True},
        {'key': 'body_uk', 'type': 'textarea', 'label': 'Текст (укр)'},
        {'key': 'body_ru', 'type': 'textarea', 'label': 'Текст (рос)'},
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
        {'key': 'title_uk', 'type': 'text', 'label': 'Заголовок (укр)', 'required': True},
        {'key': 'title_ru', 'type': 'text', 'label': 'Заголовок (рос)'},
    ),
}

SCHEMA_DEALER_SUPPORT = {
    'kind': 'dealer_support',
    'upload_to': '',
    'add_label': 'Додати пункт підтримки',
    'fields': (
        {'key': 'title_uk', 'type': 'text', 'label': 'Заголовок (укр)', 'required': True},
        {'key': 'title_ru', 'type': 'text', 'label': 'Заголовок (рос)'},
        {'key': 'body_uk', 'type': 'textarea', 'label': 'Текст (укр)'},
        {'key': 'body_ru', 'type': 'textarea', 'label': 'Текст (рос)'},
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


class CmsJsonListWidget(Widget):
    template_name = 'django/forms/widgets/cms_json_list.html'

    class Media:
        css = {'all': ('css/admin/cms_json_list.css',)}
        js = ('js/admin/cms_json_list.js',)

    def __init__(self, schema: dict[str, Any], attrs: dict[str, Any] | None = None) -> None:
        self.schema = schema
        super().__init__(attrs)

    def format_value(self, value):
        if value in (None, ''):
            return '[]'
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, str):
            raw = value.strip() or '[]'
            try:
                parsed = json.loads(raw)
            except (TypeError, ValueError, json.JSONDecodeError):
                return '[]'
            return json.dumps(parsed, ensure_ascii=False)
        return '[]'

    def value_from_datadict(self, data, files, name):
        raw = data.get(name, '[]')
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, list):
            try:
                raw = json.loads(raw or '[]')
            except (TypeError, ValueError, json.JSONDecodeError):
                return []
        if not isinstance(raw, list):
            return []
        cleaned = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            if all(str(v or '').strip() == '' for v in item.values()):
                continue
            cleaned.append(item)
        return cleaned

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
