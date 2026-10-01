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

    def test_beds_and_poufs_have_no_subcategories(self):
        from catalog.models import Category

        beds = Category.objects.get(slug='lizhka', parent=None)
        poufs = Category.objects.get(slug='pufy', parent=None)
        sofas = Category.objects.get(slug='divany', parent=None)

        self.assertEqual(beds.children.count(), 0)
        self.assertEqual(poufs.children.count(), 0)
        self.assertGreaterEqual(sofas.children.filter(is_active=True).count(), 3)

        beds_page = self.client.get('/katalog/lizhka/')
        poufs_page = self.client.get('/katalog/pufy/')
        sofas_page = self.client.get('/katalog/divany/')

        self.assertNotContains(beds_page, 'catalog-filters__label">Категорія')
        self.assertNotContains(poufs_page, 'catalog-filters__label">Категорія')
        self.assertContains(sofas_page, 'Модульні')
        self.assertContains(sofas_page, 'Кутові')
        self.assertContains(sofas_page, 'Прямі')

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
