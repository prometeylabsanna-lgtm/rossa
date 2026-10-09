"""Honeypot: заповнене website → fake success без запису."""

from django.test import Client, TestCase
from django.urls import reverse

from leads.forms import HONEYPOT_FIELD
from leads.idempotency import new_idempotency_key
from leads.models import ContactLead, OrderRequest


class HoneypotTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)

    def setUp(self):
        self.client = Client()

    def test_order_honeypot_no_save(self):
        response = self.client.post(reverse('leads:order'), {
            'product_name': 'Хак',
            'product_slug': 'milan',
            'fabric_name': '1',
            'shade_name': 'Беж',
            'sku': 'x',
            'price': 1,
            'name': 'Іван Петренко',
            'phone': '+380441234567',
            'consent': 'on',
            'fulfillment': 'pickup',
            'idempotency_key': new_idempotency_key(),
            HONEYPOT_FIELD: 'https://spam.example',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OrderRequest.objects.count(), 0)

    def test_contact_honeypot_no_save(self):
        response = self.client.post(reverse('leads:contact'), {
            'name': 'Олена',
            'phone': '+380501112233',
            'message': 'спам',
            'consent': 'on',
            'idempotency_key': new_idempotency_key(),
            HONEYPOT_FIELD: 'bot',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactLead.objects.count(), 0)

    def test_order_empty_honeypot_ok(self):
        response = self.client.post(reverse('leads:order'), {
            'product_name': 'Хак',
            'product_slug': 'milan',
            'fabric_name': '1',
            'shade_name': 'Беж',
            'sku': 'x',
            'price': 1,
            'name': 'Іван Петренко',
            'phone': '+380441234567',
            'consent': 'on',
            'fulfillment': 'pickup',
            'idempotency_key': new_idempotency_key(),
            HONEYPOT_FIELD: '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OrderRequest.objects.count(), 1)
