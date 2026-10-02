"""Віджет редагування лейблів/підказок форми співпраці."""

from __future__ import annotations

import json
from typing import Any

from django.forms.widgets import Widget

from core.collab_form_copy import (
    FORM_FIELD_KEYS,
    FORM_FIELD_TITLES,
    default_collab_form_copy,
    normalize_collab_form_copy,
)

FORM_COPY_SCHEMA = {
    'kind': 'form_copy',
    'rows': [
        {
            'key': key,
            'title': FORM_FIELD_TITLES[key],
            'has_placeholder': key != 'submit',
        }
        for key in FORM_FIELD_KEYS
    ],
}


class CmsFormCopyWidget(Widget):
    template_name = 'django/forms/widgets/cms_form_copy.html'

    class Media:
        css = {'all': ('css/admin/cms_json_list.css', 'css/admin/cms_form_copy.css')}
        js = ('js/admin/cms_form_copy.js',)

    def format_value(self, value):
        return json.dumps(normalize_collab_form_copy(value), ensure_ascii=False)

    def value_from_datadict(self, data, files, name):
        raw = data.get(name, '{}')
        if isinstance(raw, dict):
            return normalize_collab_form_copy(raw)
        try:
            parsed = json.loads(raw or '{}')
        except (TypeError, ValueError, json.JSONDecodeError):
            return default_collab_form_copy()
        return normalize_collab_form_copy(parsed)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        normalized = normalize_collab_form_copy(value)
        formatted = json.dumps(normalized, ensure_ascii=False)
        context['widget']['value'] = formatted
        context['widget']['items_json'] = formatted
        context['widget']['schema_json'] = json.dumps(FORM_COPY_SCHEMA, ensure_ascii=False)
        return context
