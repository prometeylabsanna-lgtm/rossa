"""Валідація імені та UA-телефону для публічних форм."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MSG_NAME_INVALID = _(
    'Ім’я не може містити цифри або спецсимволи. Будь ласка, використовуйте лише букви'
)
MSG_PHONE_INVALID = _(
    'Введіть коректний номер мобільного телефону у форматі +380 (XX) XXX-XX-XX'
)
MSG_REQUIRED = _('Поле обов’язкове для заповнення')
MSG_EMAIL_INVALID = _('Введіть коректний e-mail')

# Букви (усі алфавіти) + пробіл / дефіс / апострофи між частинами імені
_NAME_RE = re.compile(
    r"^[^\W\d_]+(?:[-'’ʼ\s]+[^\W\d_]+)*$",
    re.UNICODE,
)
_DIGIT_RE = re.compile(r'\d')
_PHONE_E164_RE = re.compile(r'^\+380\d{9}$')


def normalize_ua_phone(value: str) -> str | None:
    """Нормалізує введення до +380XXXXXXXXX або None."""
    digits = re.sub(r'\D', '', value or '')
    if digits.startswith('380') and len(digits) == 12:
        return f'+{digits}'
    if digits.startswith('80') and len(digits) == 11:
        return f'+3{digits}'
    if digits.startswith('0') and len(digits) == 10:
        return f'+38{digits}'
    if len(digits) == 9:
        return f'+380{digits}'
    return None


def validate_person_name(value: str) -> str:
    text = (value or '').strip()
    if not text:
        raise ValidationError(MSG_REQUIRED, code='required')
    if _DIGIT_RE.search(text) or not _NAME_RE.match(text):
        raise ValidationError(MSG_NAME_INVALID, code='invalid')
    return re.sub(r'\s+', ' ', text)


def validate_ua_phone(value: str) -> str:
    text = (value or '').strip()
    if not text:
        raise ValidationError(MSG_REQUIRED, code='required')
    normalized = normalize_ua_phone(text)
    if not normalized or not _PHONE_E164_RE.match(normalized):
        raise ValidationError(MSG_PHONE_INVALID, code='invalid')
    return normalized
