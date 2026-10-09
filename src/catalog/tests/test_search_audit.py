"""Аудит пошуку: slug, кирилиця, ліміт довжини."""

from django.test import Client, TestCase
from django.urls import reverse

from catalog.selectors import SEARCH_QUERY_MAX, search_products


class SearchAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)

    def setUp(self):
        self.client = Client()

    def test_slug_search(self):
        found = search_products('milan')
        self.assertTrue(found.filter(slug='milan').exists())

    def test_cyrillic_lowercase_finds_title_case(self):
        self.assertTrue(search_products('мілан').filter(slug='milan').exists())

    def test_long_query_truncated_not_500(self):
        q = 'м' * (SEARCH_QUERY_MAX + 200)
        response = self.client.get(reverse('catalog:search'), {'q': q})
        self.assertEqual(response.status_code, 200)

    def test_inactive_not_in_search(self):
        from catalog.models import Product
        Product.objects.filter(slug='milan').update(is_active=False)
        self.assertFalse(search_products('milan').exists())
