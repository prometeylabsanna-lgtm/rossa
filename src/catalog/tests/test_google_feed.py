"""Фід Google Merchant Center."""
import shutil
import tempfile
import xml.etree.ElementTree as ET
from io import BytesIO

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from catalog.google_feed import cap_image_urls
from catalog.models import Category, Product, ProductColor, ProductColorOption

G_NS = 'http://base.google.com/ns/1.0'
FEED_URL = '/feeds/google-merchant.xml'
TMP_MEDIA = tempfile.mkdtemp(prefix='rossa_gfeed_')


def _g(item, tag):
    return item.findtext(f'{{{G_NS}}}{tag}')


def _png(name: str) -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new('RGB', (16, 16), (180, 90, 40)).save(buf, format='PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


class GoogleFeedImageCapTests(SimpleTestCase):
    def test_additional_images_capped_at_ten(self):
        urls = [f'https://cdn.example/{index}.webp' for index in range(15)]
        urls.insert(1, urls[0])
        main, extra = cap_image_urls(urls)
        self.assertEqual(main, 'https://cdn.example/0.webp')
        self.assertEqual(len(extra), 10)
        self.assertEqual(extra[0], 'https://cdn.example/1.webp')
        self.assertNotIn(main, extra)
        self.assertEqual(cap_image_urls([]), (None, []))


@override_settings(MEDIA_ROOT=TMP_MEDIA)
class GoogleMerchantFeedTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TMP_MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()
        parent = Category.objects.create(slug='divany', name_uk='Дивани', name_ru='Диваны')
        child = Category.objects.create(
            slug='kutovi',
            name_uk='Кутові',
            name_ru='Угловые',
            parent=parent,
        )
        self.active = Product.objects.create(
            slug='milan',
            sku='SOFA-1',
            name_uk='Мілан',
            name_ru='Милан',
            category=child,
            base_price=1234,
            is_active=True,
            is_available=True,
            description_uk=(
                '<script>alert(1)</script><p>Мякий &amp; зручний</p><strong>диван</strong>'
            ),
            description_ru='<p>Секретный русский</p>',
        )
        Product.objects.create(
            slug='hidden-sofa',
            sku='HIDDEN',
            name_uk='Прихований',
            category=child,
            base_price=999,
            is_active=False,
            is_available=True,
            description_uk='<p>не показувати</p>',
        )
        self.unavailable = Product.objects.create(
            slug='oslo',
            sku='SOFA-2',
            name_uk='Осло',
            category=child,
            base_price=2500,
            is_active=True,
            is_available=False,
            description_uk='Немає на складі',
        )

    def tearDown(self):
        cache.clear()

    def _response(self, **extra):
        return self.client.get(FEED_URL, **extra)

    def _items(self, response):
        root = ET.fromstring(response.content)
        return root, root.findall('channel/item')

    def _by_id(self, items, feed_id):
        for item in items:
            if _g(item, 'id') == feed_id:
                return item
        self.fail(f'item {feed_id} відсутній у фіді')

    def test_feed_is_valid_xml_with_required_fields(self):
        self.assertEqual(reverse('google_merchant_feed'), FEED_URL)
        response = self._response()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml; charset=utf-8')
        self.assertIn('max-age=1800', response['Cache-Control'])
        root, items = self._items(response)
        self.assertEqual(root.tag, 'rss')
        self.assertEqual(root.attrib.get('version'), '2.0')
        self.assertIn(b'xmlns:g="http://base.google.com/ns/1.0"', response.content)
        channel = root.find('channel')
        self.assertEqual(channel.findtext('title'), 'ROSSA')
        self.assertEqual(channel.findtext('link'), 'http://testserver/')
        self.assertEqual(channel.findtext('description'), 'Каталог меблів ROSSA')
        self.assertEqual(len(items), 2)
        self.assertEqual(self.client.get('/ru/feeds/google-merchant.xml').status_code, 404)
        for item in items:
            for tag in ('title', 'description', 'link'):
                self.assertTrue((item.findtext(tag) or '').strip(), tag)
            for tag in ('id', 'price', 'availability', 'condition', 'brand', 'product_type'):
                self.assertTrue((_g(item, tag) or '').strip(), tag)
            self.assertTrue(item.findtext('link').startswith('http://testserver/tovar/'))
            self.assertNotIn('/ru/', item.findtext('link'))
            self.assertIn(_g(item, 'availability'), {'in_stock', 'out_of_stock'})
            self.assertEqual(_g(item, 'condition'), 'new')
            self.assertEqual(_g(item, 'brand'), 'Rossa')
            self.assertEqual(_g(item, 'product_type'), 'Дивани > Кутові')
            self.assertRegex(_g(item, 'price'), r'^\d+\.\d{2} UAH$')
        active = self._by_id(items, 'SOFA-1')
        self.assertEqual(active.findtext('title'), 'Мілан')
        self.assertEqual(active.findtext('link'), 'http://testserver/tovar/milan/')
        self.assertEqual(_g(active, 'availability'), 'in_stock')
        missing = self._by_id(items, 'SOFA-2')
        self.assertEqual(_g(missing, 'availability'), 'out_of_stock')

    def test_price_format(self):
        _, items = self._items(self._response())
        self.assertEqual(_g(self._by_id(items, 'SOFA-1'), 'price'), '1234.00 UAH')
        self.assertEqual(_g(self._by_id(items, 'SOFA-2'), 'price'), '2500.00 UAH')

    def test_inactive_products_excluded(self):
        response = self._response()
        _, items = self._items(response)
        ids = {_g(item, 'id') for item in items}
        self.assertEqual(ids, {'SOFA-1', 'SOFA-2'})
        body = response.content.decode()
        self.assertNotIn('HIDDEN', body)
        self.assertNotIn('Прихований', body)
        self.assertNotIn('hidden-sofa', body)
        self.assertNotIn('не показувати', body)

    def test_description_html_is_stripped(self):
        response = self._response(HTTP_ACCEPT_LANGUAGE='ru')
        _, items = self._items(response)
        description = self._by_id(items, 'SOFA-1').findtext('description')
        self.assertEqual(description, 'Мякий & зручний диван')
        self.assertNotIn('<', description)
        self.assertNotIn('>', description)
        self.assertNotIn('alert', description)
        body = response.content.decode()
        self.assertIn('Мякий &amp; зручний диван', body)
        self.assertNotIn('&amp;amp;', body)
        self.assertNotIn('<p>', body)
        self.assertNotIn('<strong>', body)
        self.assertNotIn('Секретный русский', body)
        self.assertNotIn('/ru/tovar/', body)

    def test_image_links_are_absolute_and_skip_inactive_color(self):
        self.active.default_image.save('main.png', _png('main.png'), save=True)
        beige = ProductColorOption.objects.create(
            slug='bezh',
            name_uk='Беж',
            hex_color='#D8C3A5',
        )
        hidden = ProductColorOption.objects.create(
            slug='hidden-shade',
            name_uk='Темний',
            hex_color='#222222',
        )
        ProductColor.objects.create(
            product=self.active,
            color=beige,
            image=_png('extra.png'),
            is_active=True,
        )
        ProductColor.objects.create(
            product=self.active,
            color=hidden,
            image=_png('secret-shade.png'),
            is_active=False,
        )
        cache.clear()
        response = self._response()
        _, items = self._items(response)
        item = self._by_id(items, 'SOFA-1')
        image = _g(item, 'image_link')
        self.assertTrue(image.startswith('http://testserver/media/'))
        self.assertIn('main.webp', image)
        extra = item.findall(f'{{{G_NS}}}additional_image_link')
        self.assertEqual(len(extra), 1)
        self.assertTrue(extra[0].text.startswith('http://testserver/media/'))
        self.assertIn('extra.webp', extra[0].text)
        self.assertNotIn('secret-shade', response.content.decode())

    def test_response_is_cached_until_cache_cleared(self):
        first = self._response()
        self.active.base_price = 5000
        self.active.save(update_fields=['base_price'])
        cached = self._response()
        self.assertEqual(cached.content, first.content)
        cache.clear()
        fresh = self._response()
        self.assertIn(b'5000.00 UAH', fresh.content)
        self.assertNotIn(b'1234.00 UAH', fresh.content)
