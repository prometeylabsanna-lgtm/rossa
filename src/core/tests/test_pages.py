from django.test import Client, TestCase
from django.urls import reverse


class PagesSmokeTests(TestCase):
    def setUp(self):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)
        self.client = Client()

    def test_home(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)

    def test_catalog_tree(self):
        for url in [
            '/katalog/',
            '/katalog/divany/',
            '/katalog/divany/modulni/',
            '/katalog/lizhka/',
            '/katalog/pufy/',
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_product(self):
        response = self.client.get('/tovar/milan/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Мілан')

    def test_info_pages(self):
        for name in ['core:about', 'core:collab', 'core:contacts', 'core:thanks', 'core:delivery', 'core:offer', 'core:privacy']:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

    def test_robots_and_health(self):
        self.assertEqual(self.client.get('/robots.txt').status_code, 200)
        self.assertEqual(self.client.get('/healthz/').status_code, 200)
        self.assertEqual(self.client.get('/sitemap.xml').status_code, 200)
