"""Аудит безпеки lead endpoints: CSRF, mass-assign, rate-limit."""

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from leads.idempotency import new_idempotency_key
from leads.models import ContactLead, OrderRequest
from leads.rate_limit import KEY_PREFIX


def _order_data(**overrides):
    data = {
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
    }
    data.update(overrides)
    return data


class LeadSecurityAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        cache.clear()

    def test_csrf_required(self):
        response = self.client.post(reverse('leads:order'), _order_data())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(OrderRequest.objects.count(), 0)

    def test_status_mass_assign_ignored(self):
        client = Client()
        response = client.post(
            reverse('leads:order'),
            _order_data(status='done', language='xx'),
        )
        self.assertEqual(response.status_code, 302)
        lead = OrderRequest.objects.get()
        self.assertEqual(lead.status, 'new')
        self.assertEqual(lead.language, 'uk')

    @override_settings(LEAD_RATE_LIMIT_MAX=3)
    def test_rate_limit_returns_429(self):
        client = Client()
        url = reverse('leads:contact')
        for _ in range(3):
            r = client.post(url, {
                'name': 'Олена',
                'phone': '+380501112233',
                'message': 'тест',
                'consent': 'on',
                'idempotency_key': new_idempotency_key(),
            })
            self.assertIn(r.status_code, (302, 400))
        blocked = client.post(url, {
            'name': 'Олена',
            'phone': '+380501112233',
            'message': 'тест',
            'consent': 'on',
            'idempotency_key': new_idempotency_key(),
        })
        self.assertEqual(blocked.status_code, 429)
        self.assertLessEqual(ContactLead.objects.count(), 3)
        self.assertTrue(cache.get(f'{KEY_PREFIX}127.0.0.1') or cache.get(f'{KEY_PREFIX}unknown'))
