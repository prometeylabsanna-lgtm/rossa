from django.test import Client, TestCase
from django.urls import reverse

from leads.forms import ContactForm, OrderForm
from leads.idempotency import new_idempotency_key
from leads.models import ContactLead, OrderRequest, PartnershipLead
from leads.validators import normalize_ua_phone, validate_person_name, validate_ua_phone


def _order_data(**overrides):
    data = {
        'product_name': 'Мілан',
        'product_slug': 'milan',
        'fabric_name': '1',
        'shade_name': 'Беж',
        'price': 1,
        'sku': 'hacked',
        'name': 'Іван Петренко',
        'phone': '+380441234567',
        'consent': 'on',
        'fulfillment': 'pickup',
        'idempotency_key': new_idempotency_key(),
    }
    data.update(overrides)
    return data


class ValidatorUnitTests(TestCase):
    def test_normalize_phone(self):
        self.assertEqual(normalize_ua_phone('+380501112233'), '+380501112233')
        self.assertEqual(normalize_ua_phone('0501112233'), '+380501112233')
        self.assertEqual(normalize_ua_phone('50 111 22 33'), '+380501112233')
        self.assertIsNone(normalize_ua_phone('050111'))

    def test_name_rejects_digits(self):
        with self.assertRaises(Exception):
            validate_person_name('Іван2')
        self.assertEqual(validate_person_name("О’Коннор"), "О’Коннор")
        self.assertEqual(validate_person_name('Анна-Марія'), 'Анна-Марія')

    def test_phone_ok(self):
        self.assertEqual(validate_ua_phone('+38 (050) 111 - 22 - 33'), '+380501112233')


class LeadFormTests(TestCase):
    def setUp(self):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)
        self.client = Client()

    def test_order_requires_phone(self):
        response = self.client.post(reverse('leads:order'), _order_data(phone='', name='Іван'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OrderRequest.objects.count(), 0)

    def test_order_rejects_name_with_digits(self):
        response = self.client.post(reverse('leads:order'), _order_data(name='Іван2'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OrderRequest.objects.count(), 0)
        form = OrderForm(_order_data(name='Іван2'))
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_order_rejects_short_phone(self):
        form = OrderForm(_order_data(name='Іван', phone='+38050111'))
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_order_ok_server_price(self):
        response = self.client.post(reverse('leads:order'), _order_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OrderRequest.objects.count(), 1)
        lead = OrderRequest.objects.get()
        self.assertEqual(lead.phone, '+380441234567')
        self.assertEqual(lead.price, 42900)
        self.assertEqual(lead.sku, 'MILAN-1')

    def test_contact_ok(self):
        response = self.client.post(reverse('leads:contact'), {
            'name': 'Олена',
            'phone': '+380501112233',
            'message': 'Питання по дивану',
            'consent': 'on',
            'idempotency_key': new_idempotency_key(),
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactLead.objects.count(), 1)

    def test_contact_form_normalizes_phone(self):
        form = ContactForm({
            'name': 'Олена',
            'phone': '0501112233',
            'message': 'Питання',
            'consent': 'on',
            'idempotency_key': new_idempotency_key(),
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['phone'], '+380501112233')

    def test_partnership_ok(self):
        response = self.client.post(reverse('leads:partnership'), {
            'name': 'Олена',
            'phone': '+380671112233',
            'email': 'partner@example.com',
            'city': 'Київ',
            'message': 'Хочу стати дилером',
            'idempotency_key': new_idempotency_key(),
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PartnershipLead.objects.count(), 1)
        lead = PartnershipLead.objects.get()
        self.assertEqual(lead.name, 'Олена')
        self.assertEqual(lead.company, 'Олена')
        self.assertTrue(lead.consent)
