"""Edge cases: PDP, варіації тканини/кольору, наявність."""

from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import Product


class ProductDetailEdgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)

    def setUp(self):
        self.client = Client()
        self.product = Product.objects.get(slug='milan')

    def test_inactive_product_404(self):
        self.product.is_active = False
        self.product.save(update_fields=['is_active'])
        response = self.client.get(reverse('catalog:product', kwargs={'slug': 'milan'}))
        self.assertEqual(response.status_code, 404)

    def test_unavailable_disables_order_button(self):
        self.product.is_available = False
        self.product.save(update_fields=['is_available'])
        response = self.client.get(reverse('catalog:product', kwargs={'slug': 'milan'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Немає в наявності')
        self.assertContains(response, 'data-open-order')
        self.assertContains(response, 'disabled')
        self.assertFalse(response.context['product'].is_available)

    def test_fabric_switch_updates_price_and_sku(self):
        response = self.client.get(reverse('catalog:product', kwargs={'slug': 'milan'}))
        self.assertEqual(response.status_code, 200)
        fabrics = response.context['fabrics']
        self.assertTrue(fabrics)
        fabric = fabrics[-1] if len(fabrics) > 1 else fabrics[0]
        switched = self.client.get(
            reverse('catalog:product', kwargs={'slug': 'milan'}),
            {'fabric': fabric.id},
        )
        self.assertEqual(switched.status_code, 200)
        self.assertEqual(switched.context['selected_fabric'].id, fabric.id)
        expected = self.product.price_for_fabric(fabric)
        self.assertEqual(switched.context['price'], expected)

    def test_invalid_fabric_falls_back(self):
        response = self.client.get(
            reverse('catalog:product', kwargs={'slug': 'milan'}),
            {'fabric': '999999', 'color': 'not-a-number'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['selected_fabric'])

    def test_color_switch_htmx_partial(self):
        response = self.client.get(reverse('catalog:product', kwargs={'slug': 'milan'}))
        colors = response.context['colors']
        self.assertTrue(colors)
        color_id = colors[-1]['id']
        htmx = self.client.get(
            reverse('catalog:product', kwargs={'slug': 'milan'}),
            {'color': color_id},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(htmx.status_code, 200)
        names = [t.name for t in htmx.templates]
        self.assertTrue(any(n.endswith('product_config.html') for n in names))
        self.assertEqual(htmx.context['selected_color']['id'], color_id)

    def test_order_form_prefill_snapshot(self):
        response = self.client.get(reverse('catalog:product', kwargs={'slug': 'milan'}))
        form = response.context['form']
        self.assertEqual(form.initial.get('product_slug'), 'milan')
        self.assertEqual(form.initial.get('product_name'), self.product.name)
        self.assertIsNotNone(form.initial.get('price'))
