"""Edge cases: фільтри, пагінація, пошук, сортування каталогу."""

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from catalog.models import Product
from catalog.selectors import SORT_MAP, apply_sort, search_products, visible_products


@override_settings(CATALOG_PAGE_SIZE=3)
class CatalogListingEdgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)

    def setUp(self):
        self.client = Client()

    def test_combined_filters_ok(self):
        url = reverse('catalog:index')
        response = self.client.get(url, {
            'cat': 'divany',
            'price_min': '10000',
            'price_max': '200000',
            'available': '1',
            'sort': 'price-asc',
        })
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.context['total'], 0)

    def test_price_min_gt_max_empty_not_500(self):
        response = self.client.get(reverse('catalog:index'), {
            'price_min': '999999',
            'price_max': '1',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 0)
        self.assertEqual(list(response.context['products']), [])

    def test_invalid_price_params_ignored(self):
        response = self.client.get(reverse('catalog:index'), {
            'price_min': 'abc',
            'price_max': '1.5',
            'available': 'yes',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['available'])
        self.assertEqual(response.context['price_min'], '')
        self.assertEqual(response.context['price_max'], '')

    def test_offset_garbage_not_500(self):
        for bad in ('abc', '1.5', '-9', 'NULL', '%'):
            with self.subTest(offset=bad):
                response = self.client.get(reverse('catalog:index'), {'offset': bad})
                self.assertEqual(response.status_code, 200, bad)

    def test_offset_beyond_total_empty_page(self):
        total = visible_products().count()
        response = self.client.get(reverse('catalog:index'), {'offset': total + 100})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['products']), [])
        self.assertFalse(response.context['has_more'])

    def test_deactivate_product_mid_pagination(self):
        response = self.client.get(reverse('catalog:index'), {'sort': 'name'})
        self.assertEqual(response.status_code, 200)
        first_ids = [p.pk for p in response.context['products']]
        self.assertTrue(first_ids)

        Product.objects.filter(pk=first_ids[0]).update(is_active=False)
        page2 = self.client.get(reverse('catalog:index'), {
            'sort': 'name',
            'offset': 3,
        })
        self.assertEqual(page2.status_code, 200)
        page2_ids = [p.pk for p in page2.context['products']]
        self.assertNotIn(first_ids[0], page2_ids)

    def test_unknown_sort_falls_back_to_popular(self):
        response = self.client.get(reverse('catalog:index'), {'sort': 'hack;drop'})
        self.assertEqual(response.status_code, 200)
        qs = apply_sort(visible_products(), 'hack;drop')
        self.assertEqual(tuple(qs.query.order_by), SORT_MAP['popular'])

    def test_stable_sort_no_dupes_across_pages(self):
        qs = apply_sort(visible_products(), 'price-asc')
        ids = list(qs.values_list('id', flat=True))
        self.assertEqual(len(ids), len(set(ids)))

        page1 = self.client.get(reverse('catalog:index'), {'sort': 'price-asc'})
        page2 = self.client.get(reverse('catalog:index'), {
            'sort': 'price-asc',
            'offset': 3,
        })
        ids1 = [p.pk for p in page1.context['products']]
        ids2 = [p.pk for p in page2.context['products']]
        self.assertFalse(set(ids1) & set(ids2))

    def test_htmx_load_more_partial(self):
        response = self.client.get(
            reverse('catalog:index'),
            {'offset': 3, 'sort': 'popular'},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        names = [t.name for t in response.templates]
        self.assertTrue(any(n.endswith('product_more.html') for n in names))


class CatalogSearchEdgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)

    def setUp(self):
        self.client = Client()

    def test_sql_injection_payload_safe(self):
        payload = "' OR 1=1 --"
        response = self.client.get(reverse('catalog:search'), {'q': payload})
        self.assertEqual(response.status_code, 200)
        # ORM: рядок шукається як літерал, не як умова
        self.assertEqual(list(search_products(payload)), [])

    def test_xss_escaped_in_response(self):
        payload = '<script>alert(1)</script>'
        response = self.client.get(reverse('catalog:search'), {'q': payload})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')

    def test_emoji_and_special_chars(self):
        for q in ('🔥', '%', '&', 'NULL', '   '):
            with self.subTest(q=q):
                response = self.client.get(reverse('catalog:search'), {'q': q})
                self.assertEqual(response.status_code, 200)

    def test_case_insensitive_sku_ascii(self):
        # ASCII icontains стабільний; кирилиця на SQLite залежить від collation.
        lower = search_products('milan')
        upper = search_products('MILAN')
        self.assertTrue(lower.exists())
        self.assertEqual(
            set(lower.values_list('pk', flat=True)),
            set(upper.values_list('pk', flat=True)),
        )

    def test_cyrillic_exact_case_finds_name(self):
        self.assertTrue(search_products('Мілан').exists())
        self.assertTrue(search_products('мілан').exists())

    def test_sku_search(self):
        product = Product.objects.filter(is_active=True).exclude(sku='').first()
        self.assertIsNotNone(product)
        found = search_products(product.sku)
        self.assertIn(product.pk, found.values_list('pk', flat=True))

    def test_layout_mismatch_no_fuzzy(self):
        # Немає fuzzy / layout-коректора — кирилиця «vbkfy» ≠ «milan»
        self.assertFalse(search_products('vbkfy').exists())
        self.assertTrue(search_products('milan').exists() or search_products('Мілан').exists())
