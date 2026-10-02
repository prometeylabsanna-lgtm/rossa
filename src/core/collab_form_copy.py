"""Тексти полів форми співпраці (лейбли / підказки / кнопка)."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from django.utils.translation import get_language

FORM_FIELD_KEYS = ('name', 'phone', 'email', 'city', 'message', 'submit')

FORM_FIELD_TITLES = {
    'name': 'Ім’я',
    'phone': 'Телефон',
    'email': 'Електронна адреса',
    'city': 'Місто',
    'message': 'Повідомлення',
    'submit': 'Кнопка «Надіслати»',
}

DEFAULT_COLLAB_FORM_COPY: dict[str, dict[str, str]] = {
    'name': {
        'label_uk': 'Ім’я',
        'label_ru': 'Имя',
        'placeholder_uk': 'введіть ім’я',
        'placeholder_ru': 'введите имя',
    },
    'phone': {
        'label_uk': 'Телефон',
        'label_ru': 'Телефон',
        'placeholder_uk': '50 123 4567',
        'placeholder_ru': '50 123 4567',
    },
    'email': {
        'label_uk': 'Електронна адреса',
        'label_ru': 'Электронная почта',
        'placeholder_uk': 'введіть електронну адресу',
        'placeholder_ru': 'введите электронную почту',
    },
    'city': {
        'label_uk': 'Місто',
        'label_ru': 'Город',
        'placeholder_uk': 'введіть місто',
        'placeholder_ru': 'введите город',
    },
    'message': {
        'label_uk': 'Повідомлення',
        'label_ru': 'Сообщение',
        'placeholder_uk': 'введіть повідомлення',
        'placeholder_ru': 'введите сообщение',
    },
    'submit': {
        'label_uk': 'Надіслати',
        'label_ru': 'Отправить',
        'placeholder_uk': '',
        'placeholder_ru': '',
    },
}


def default_collab_form_copy() -> dict[str, dict[str, str]]:
    return deepcopy(DEFAULT_COLLAB_FORM_COPY)


def normalize_collab_form_copy(raw: Any) -> dict[str, dict[str, str]]:
    base = default_collab_form_copy()
    if not isinstance(raw, dict):
        return base
    for key in FORM_FIELD_KEYS:
        item = raw.get(key)
        if not isinstance(item, dict):
            continue
        for attr in ('label_uk', 'label_ru', 'placeholder_uk', 'placeholder_ru'):
            value = item.get(attr)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                base[key][attr] = text
    return base


def resolve_form_field_copy(
    copy: dict[str, dict[str, str]] | None,
    field_key: str,
    *,
    language: str | None = None,
) -> dict[str, str]:
    data = normalize_collab_form_copy(copy)
    item = data.get(field_key) or DEFAULT_COLLAB_FORM_COPY[field_key]
    lang = (language or get_language() or 'uk').split('-')[0]
    if lang not in {'uk', 'ru'}:
        lang = 'uk'
    label = (item.get(f'label_{lang}') or item.get('label_uk') or '').strip()
    placeholder = (item.get(f'placeholder_{lang}') or item.get('placeholder_uk') or '').strip()
    return {'label': label, 'placeholder': placeholder}
