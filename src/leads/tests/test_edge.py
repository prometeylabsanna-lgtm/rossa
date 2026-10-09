"""Edge cases: сверка каталогу, ідемпотентність, валідація payload."""

from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Product
from leads.forms import OrderForm
from leads.idempotency import new_idempotency_key
from leads.models import ContactLead, OrderRequest, PartnershipLead


def _order_data(**overrides):
    data = {
        'product_name': 'Хак',
        'product_slug': 'milan',
        'fabric_name': '1',
        'shade_name': 'Беж',
        'sku': 'hacked',
        'price': 1,
        'name': 'Іван Петренко',
        'phone': '+380441234567',
        'consent': 'on',
        'fulfillment': 'pickup',
        'idempotency_key': new_idempotency_key(),
    }
    data.update(overrides)
    return data


class OrderLeadEdgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)

    def setUp(self):
        self.client = Client()

    def test_negative_price_overwritten_by_catalog(self):
        form = OrderForm(_order_data(price=-5))
        # Negative fails field validation before clean snapshot
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    def test_fractional_price_rejected(self):
        form = OrderForm(_order_data(price='1.5'))
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    def test_non_numeric_price_rejected(self):
        form = OrderForm(_order_data(price='abc'))
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    def test_price_tampering_replaced_with_catalog(self):
        response = self.client.post(reverse('leads:order'), _order_data(price=1))
        self.assertEqual(response.status_code, 302)
        lead = OrderRequest.objects.get()
        self.assertEqual(lead.price, 42900)
        self.assertEqual(lead.product_name, 'Мілан')
        self.assertEqual(lead.sku, 'MILAN-1')

    def test_orphan_product_slug_rejected(self):
        response = self.client.post(
            reverse('leads:order'),
            _order_data(product_slug='deleted-product', product_name='Видалений'),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OrderRequest.objects.count(), 0)

    def test_unavailable_product_allows_consultation_lead(self):
        """UI блокує «Замовити»; консультація / preorder на бекенді дозволені."""
        Product.objects.filter(slug='milan').update(is_available=False)
        response = self.client.post(reverse('leads:order'), _order_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OrderRequest.objects.count(), 1)
        self.assertEqual(OrderRequest.objects.get().price, 42900)

    def test_double_post_same_key_one_lead(self):
        data = _order_data()
        url = reverse('leads:order')
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(OrderRequest.objects.count(), 1)

    def test_double_post_different_keys_two_leads(self):
        url = reverse('leads:order')
        self.assertEqual(self.client.post(url, _order_data()).status_code, 302)
        self.assertEqual(self.client.post(url, _order_data()).status_code, 302)
        self.assertEqual(OrderRequest.objects.count(), 2)

    def test_sql_injection_in_name_rejected(self):
        form = OrderForm(_order_data(name="Robert'; DROP TABLE--"))
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_emoji_name_rejected(self):
        form = OrderForm(_order_data(name='Іван 🔥'))
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_get_not_allowed(self):
        response = self.client.get(reverse('leads:order'))
        self.assertEqual(response.status_code, 405)

    def test_contact_xss_message_persisted(self):
        payload = '<img src=x onerror=alert(1)>'
        response = self.client.post(reverse('leads:contact'), {
            'name': 'Олена',
            'phone': '+380501112233',
            'message': payload,
            'consent': 'on',
            'idempotency_key': new_idempotency_key(),
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactLead.objects.get().message, payload)

    def test_contact_double_post_same_key_one_lead(self):
        data = {
            'name': 'Олена',
            'phone': '+380501112233',
            'message': 'Питання',
            'consent': 'on',
            'idempotency_key': new_idempotency_key(),
        }
        url = reverse('leads:contact')
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(ContactLead.objects.count(), 1)

    def test_partnership_double_post_same_key_one_lead(self):
        data = {
            'name': 'Олена',
            'phone': '+380671112233',
            'email': 'partner@example.com',
            'city': 'Київ',
            'message': 'Дилер',
            'idempotency_key': new_idempotency_key(),
        }
        url = reverse('leads:partnership')
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.assertEqual(PartnershipLead.objects.count(), 1)

    def test_htmx_success_sets_redirect_header(self):
        response = self.client.post(
            reverse('leads:order'),
            _order_data(),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Redirect'], reverse('core:thanks'))

    def test_xss_in_comment_stored(self):
        payload = '<script>alert(1)</script>'
        response = self.client.post(reverse('leads:order'), _order_data(comment=payload))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OrderRequest.objects.get().comment, payload)
