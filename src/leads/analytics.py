"""Подія generate_lead для GTM: лише після реального збереження заявки."""

from __future__ import annotations

import json

from leads.validators import normalize_ua_phone

SESSION_KEY = 'rossa_generate_lead'
HX_EVENT = 'leadSubmitted'

FORM_ID_CONTACT = 'contact_form'
FORM_ID_ORDER = 'order_form'
FORM_ID_PARTNERSHIP = 'partnership_form'


def lead_event_payload(form, form_id: str) -> dict:
    """Збирає form_id + user_data (порожній email — порожній рядок, телефон у E.164)."""
    data = getattr(form, 'cleaned_data', None) or {}
    email = (data.get('email') or '').strip()
    if not email:
        instance = getattr(form, 'instance', None)
        email = (getattr(instance, 'email', None) or '').strip()
    phone_raw = data.get('phone') or ''
    phone = normalize_ua_phone(str(phone_raw)) or ''
    return {
        'form_id': form_id,
        'email': email,
        'phone_number': phone,
    }


def attach_lead_success(request, response, payload: dict):
    """Кладе подію в сесію (для /dyakuyemo/) і HX-Trigger (для HTMX)."""
    request.session[SESSION_KEY] = payload
    request.session.modified = True
    if getattr(request, 'htmx', False):
        response['HX-Trigger'] = json.dumps(
            {
                HX_EVENT: {
                    'form_id': payload['form_id'],
                    'email': payload['email'],
                    'phone_number': payload['phone_number'],
                }
            },
            ensure_ascii=True,
            separators=(',', ':'),
        )
    return response


def pop_lead_event(request) -> dict | None:
    return request.session.pop(SESSION_KEY, None)
