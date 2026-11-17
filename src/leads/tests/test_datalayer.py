"""generate_lead: HX-Trigger і прапорець на thanks лише після реального збереження."""

import json

from django.test import Client, TestCase
from django.urls import reverse

from leads.analytics import (
    FORM_ID_CONTACT,
    FORM_ID_ORDER,
    FORM_ID_PARTNERSHIP,
    SESSION_KEY,
)
from leads.forms import HONEYPOT_FIELD
from leads.idempotency import new_idempotency_key
from leads.models import ContactLead, OrderRequest, PartnershipLead


def _order_data(**overrides):
    data = {
        'product_name': 'Мілан',
        'product_slug': 'milan',
        'fabric_name': '1',
        'shade_name': 'Беж',
        'price': 1,
        'sku': 'hacked',
        'name': 'Іван Петренко',
        'phone': '0501112233',
        'city': 'Харків',
        'idempotency_key': new_idempotency_key(),
    }
    data.update(overrides)
    return data


def _contact_data(**overrides):
    data = {
        'name': 'Олена',
        'phone': '+380501112233',
        'city': 'Харків',
        'idempotency_key': new_idempotency_key(),
    }
    data.update(overrides)
    return data


def _partnership_data(**overrides):
    data = {
        'name': 'Олена',
        'phone': '+380671112233',
        'city': 'Київ',
        'idempotency_key': new_idempotency_key(),
    }
    data.update(overrides)
    return data


def _trigger_payload(response):
    raw = response.get('HX-Trigger')
    if not raw:
        return None
    data = json.loads(raw)
    return data.get('leadSubmitted')


class LeadDataLayerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)

    def setUp(self):
        self.client = Client()

    def _htmx_post(self, url, data):
        return self.client.post(url, data, HTTP_HX_REQUEST='true')

    def test_htmx_contact_success_trigger_and_thanks_payload(self):
        response = self._htmx_post(reverse('leads:contact'), _contact_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Redirect'], reverse('core:thanks'))
        payload = _trigger_payload(response)
        self.assertEqual(payload, {
            'form_id': FORM_ID_CONTACT,
            'email': '',
            'phone_number': '+380501112233',
        })
        self.assertEqual(ContactLead.objects.count(), 1)
        self.assertEqual(self.client.session[SESSION_KEY], payload)

        thanks = self.client.get(reverse('core:thanks'))
        self.assertEqual(thanks.status_code, 200)
        self.assertContains(thanks, 'data-lead-event')
        self.assertContains(thanks, f'data-form-id="{FORM_ID_CONTACT}"')
        self.assertContains(thanks, 'data-email=""')
        self.assertContains(thanks, 'data-phone="+380501112233"')
        self.assertContains(thanks, 'js/lead-events.js')
        self.assertNotIn(SESSION_KEY, self.client.session)

        second = self.client.get(reverse('core:thanks'))
        self.assertEqual(second.status_code, 200)
        self.assertNotContains(second, 'data-lead-event')

    def test_htmx_order_success_normalizes_phone(self):
        response = self._htmx_post(reverse('leads:order'), _order_data())
        self.assertEqual(response.status_code, 200)
        payload = _trigger_payload(response)
        self.assertEqual(payload['form_id'], FORM_ID_ORDER)
        self.assertEqual(payload['email'], '')
        self.assertEqual(payload['phone_number'], '+380501112233')
        self.assertEqual(OrderRequest.objects.count(), 1)

    def test_htmx_partnership_success_trigger(self):
        response = self._htmx_post(reverse('leads:partnership'), _partnership_data())
        self.assertEqual(response.status_code, 200)
        payload = _trigger_payload(response)
        self.assertEqual(payload, {
            'form_id': FORM_ID_PARTNERSHIP,
            'email': '',
            'phone_number': '+380671112233',
        })
        self.assertEqual(PartnershipLead.objects.count(), 1)

    def test_validation_error_has_no_trigger(self):
        response = self._htmx_post(
            reverse('leads:contact'),
            _contact_data(phone='123'),
        )
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(_trigger_payload(response))
        self.assertNotIn('HX-Redirect', response)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertEqual(ContactLead.objects.count(), 0)

        thanks = self.client.get(reverse('core:thanks'))
        self.assertNotContains(thanks, 'data-lead-event')

    def test_honeypot_success_has_no_trigger(self):
        response = self._htmx_post(
            reverse('leads:contact'),
            _contact_data(**{HONEYPOT_FIELD: 'bot'}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Redirect'], reverse('core:thanks'))
        self.assertIsNone(_trigger_payload(response))
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertEqual(ContactLead.objects.count(), 0)

    def test_duplicate_idempotency_key_does_not_refire(self):
        data = _contact_data()
        url = reverse('leads:contact')
        first = self._htmx_post(url, data)
        self.assertIsNotNone(_trigger_payload(first))
        # Знімаємо прапорець, ніби вже відвідали thanks.
        self.client.get(reverse('core:thanks'))
        self.assertNotIn(SESSION_KEY, self.client.session)

        second = self._htmx_post(url, data)
        self.assertEqual(second.status_code, 200)
        self.assertIsNone(_trigger_payload(second))
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertEqual(ContactLead.objects.count(), 1)

    def test_non_htmx_success_sets_session_without_trigger(self):
        response = self.client.post(reverse('leads:contact'), _contact_data())
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(_trigger_payload(response))
        self.assertEqual(
            self.client.session[SESSION_KEY]['form_id'],
            FORM_ID_CONTACT,
        )
