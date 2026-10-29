import json
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse


SITE = 'https://rossamebel.com.ua'


def _ld(response):
    chunks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        response.content.decode(),
        flags=re.DOTALL,
    )
    return [json.loads(chunk) for chunk in chunks]


def _types(payload):
    found = set()

    def walk(node):
        if isinstance(node, dict):
            kind = node.get('@type')
            if isinstance(kind, str):
                found.add(kind)
            elif isinstance(kind, list):
                found.update(item for item in kind if isinstance(item, str))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return found


@override_settings(SITE_URL=SITE)
class SeoFoundationTests(TestCase):
    def setUp(self):
        from django.core.management import call_command

        call_command('seed_demo', verbosity=0)
        self.client = Client()

    def test_robots_txt_groups_and_rules(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8')
        self.assertIn('User-agent: Googlebot', body)
        self.assertIn('User-agent: Bingbot', body)
        self.assertIn('User-agent: *', body)
        self.assertIn('Disallow: /poshuk/', body)
        self.assertIn('Disallow: /dyakuyemo/', body)
        self.assertIn('Disallow: /*?*sort=', body)
        self.assertIn('Disallow: /*?*price_min=', body)
        self.assertIn('Disallow: /*?*offset=', body)
        self.assertIn(f'Sitemap: {SITE}/sitemap.xml', body)
        admin = settings.ADMIN_URL.strip('/')
        self.assertNotIn(f'Disallow: /{admin}/', body)
        self.assertNotIn(admin, body)
        self.assertNotIn('FAQPage', body)

    def test_llms_txt_and_llm_redirect(self):
        llms = self.client.get('/llms.txt')
        self.assertEqual(llms.status_code, 200)
        self.assertIn('text/plain', llms['Content-Type'])
        body = llms.content.decode('utf-8')
        self.assertIn('# ROSSA', body)
        self.assertIn('/katalog/', body)
        self.assertIn('## Правила для ШІ', body)
        admin = settings.ADMIN_URL.strip('/')
        self.assertNotIn(admin, body)

        redirect = self.client.get('/llm.txt')
        self.assertEqual(redirect.status_code, 301)
        self.assertEqual(redirect['Location'], '/llms.txt')

    def test_sitemap_has_public_urls_and_alternates(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        body = response.content.decode('utf-8')
        self.assertIn(f'{SITE}/', body)
        self.assertIn(f'{SITE}/katalog/', body)
        self.assertIn(f'{SITE}/ru/katalog/', body)
        self.assertIn('/tovar/', body)
        self.assertNotIn('/dyakuyemo/', body)
        self.assertNotIn('/poshuk/', body)
        self.assertIn('hreflang="x-default"', body)

    def test_canonical_and_hreflang_home(self):
        home = self.client.get('/')
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, f'<link rel="canonical" href="{SITE}/">')
        self.assertContains(home, f'hreflang="uk" href="{SITE}/"')
        self.assertContains(home, f'hreflang="ru" href="{SITE}/ru/"')
        self.assertContains(home, f'hreflang="x-default" href="{SITE}/"')
        self.assertContains(home, 'property="og:url" content="{}/"'.format(SITE))
        self.assertEqual(home.content.decode().lower().count('<h1'), 1)
        self.assertNotContains(home, 'FAQPage')

    def test_filter_sort_are_noindex_clean_canonical(self):
        filtered = self.client.get('/katalog/?sort=price-asc&utm_source=ig')
        self.assertContains(filtered, f'<link rel="canonical" href="{SITE}/katalog/">')
        self.assertContains(filtered, 'name="robots" content="noindex,follow"')
        self.assertNotContains(filtered, f'hreflang="uk" href="{SITE}/katalog/?sort')

        clean = self.client.get('/katalog/')
        self.assertContains(clean, f'<link rel="canonical" href="{SITE}/katalog/">')
        self.assertNotContains(clean, 'name="robots" content="noindex,follow"')

    def test_search_is_noindex(self):
        response = self.client.get('/poshuk/?q=milan')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="robots" content="noindex,follow"')
        self.assertContains(response, f'<link rel="canonical" href="{SITE}/poshuk/">')

    def test_product_json_ld(self):
        response = self.client.get('/tovar/milan/')
        self.assertEqual(response.status_code, 200)
        graphs = _ld(response)
        self.assertTrue(graphs)
        types = set()
        for graph in graphs:
            types |= _types(graph)
        self.assertIn('Organization', types)
        self.assertIn('WebSite', types)
        self.assertIn('Product', types)
        self.assertIn('Offer', types)
        self.assertIn('BreadcrumbList', types)
        self.assertNotIn('FAQPage', types)
        product_nodes = []
        for graph in graphs:
            for node in graph.get('@graph', []):
                if node.get('@type') == 'Product':
                    product_nodes.append(node)
        self.assertTrue(product_nodes)
        offer = product_nodes[0]['offers']
        self.assertEqual(offer['priceCurrency'], 'UAH')
        self.assertIn('price', offer)
        self.assertIn('availability', offer)

    def test_admin_x_robots_tag(self):
        User = get_user_model()
        user = User.objects.create_superuser('seo-admin', 'seo@example.com', 'pass-seo-1')
        self.client.force_login(user)
        admin = settings.ADMIN_URL.strip('/')
        response = self.client.get(f'/{admin}/')
        self.assertIn(response.status_code, (200, 302))
        self.assertEqual(response.get('X-Robots-Tag'), 'noindex, nofollow')

    def test_thanks_noindex(self):
        response = self.client.get(reverse('core:thanks'))
        self.assertContains(response, 'name="robots" content="noindex,follow"')
        self.assertNotContains(response, 'rel="alternate" hreflang=')

    def test_home_meta_and_llms_have_pickup_not_ukraine_delivery(self):
        from core.models import HomePage

        page = HomePage.load()
        page.seo_description_uk = (
            'Дивани, ліжка та пуфи. Індивідуальний пошив тканини, доставка по Україні.'
        )
        page.seo_description_ru = (
            'Диваны, кровати и пуфы. Индивидуальный пошив ткани, доставка по Украине.'
        )
        page.save(update_fields=['seo_description_uk', 'seo_description_ru'])

        home = self.client.get('/')
        self.assertEqual(home.status_code, 200)
        body = home.content.decode('utf-8')
        self.assertNotIn('доставка по Україні', body)
        self.assertNotIn('доставка по Украине', body)
        self.assertIn('самовивіз', body.lower())

        llms = self.client.get('/llms.txt')
        llms_body = llms.content.decode('utf-8')
        self.assertNotIn('доставка по Україні', llms_body)
        self.assertIn('самовивіз', llms_body.lower())
