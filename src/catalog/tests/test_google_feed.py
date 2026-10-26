"""Фід Google Merchant Center."""
import shutil
import tempfile
import xml.etree.ElementTree as ET
from io import BytesIO

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from catalog.google_feed import FEED_CACHE_KEY, FEED_CACHE_TIMEOUT
from catalog.models import (
    Category,
    Fabric,
    Product,
    ProductColor,
    ProductColorImage,
    ProductColorOption,
    ProductFabricPrice,
)

G_NS = 'http://base.google.com/ns/1.0'
FEED_URL = '/feeds/google-merchant.xml'
TMP_MEDIA = tempfile.mkdtemp(prefix='rossa_gfeed_')


def _g(item, tag):
    return item.findtext(f'{{{G_NS}}}{tag}')


def _png(name: str) -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new('RGB', (16, 16), (180, 90, 40)).save(buf, format='PNG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/png')


def _give_image(product, name):
    product.default_image.save(name, _png(name), save=True)
    return product


def _pid(product) -> str:
    return f'rossa-{product.pk}'


@override_settings(MEDIA_ROOT=TMP_MEDIA, SITE_URL='https://rossamebel.com.ua')
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
        self.hidden = Product.objects.create(
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
        _give_image(self.active, 'active.png')
        _give_image(self.hidden, 'hidden.png')
        _give_image(self.unavailable, 'oslo.png')

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

    def _by_product(self, items, product):
        return self._by_id(items, _pid(product))

    def _assert_site_urls(self, response, *, foreign_host=None):
        base = settings.SITE_URL.strip().rstrip('/')
        prefix = f'{base}/'
        text = response.content.decode()
        self.assertTrue(base.startswith('https://'))
        self.assertNotIn('testserver', text)
        if foreign_host:
            self.assertNotIn(foreign_host, text)
        root, items = self._items(response)
        self.assertTrue(items)
        values = [root.find('channel').findtext('link')]
        for item in items:
            values.append(item.findtext('link'))
            image = _g(item, 'image_link')
            self.assertTrue(image)
            values.append(image)
            for extra in item.findall(f'{{{G_NS}}}additional_image_link'):
                self.assertTrue(extra.text)
                values.append(extra.text)
        for value in values:
            self.assertTrue(value.startswith('https://'), value)
            self.assertTrue(value.startswith(prefix), value)

    def test_feed_is_valid_xml_with_required_fields(self):
        self.assertEqual(reverse('google_merchant_feed'), FEED_URL)
        self.assertEqual(FEED_CACHE_KEY, 'catalog:google_merchant_feed:v1')
        self.assertEqual(FEED_CACHE_TIMEOUT, 30 * 60)
        response = self._response()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml; charset=utf-8')
        root, items = self._items(response)
        self.assertEqual(root.tag, 'rss')
        self.assertEqual(root.attrib.get('version'), '2.0')
        self.assertIn(b'xmlns:g="http://base.google.com/ns/1.0"', response.content)
        channel = root.find('channel')
        base = settings.SITE_URL.rstrip('/')
        self.assertEqual(channel.findtext('title'), 'ROSSA')
        self.assertEqual(channel.findtext('link'), f'{base}/')
        self.assertEqual(channel.findtext('description'), 'Каталог меблів ROSSA')
        self.assertEqual(len(items), 2)
        self.assertEqual(self.client.get('/ru/feeds/google-merchant.xml').status_code, 404)
        self._assert_site_urls(response)
        ids = [_g(item, 'id') for item in items]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {_pid(self.active), _pid(self.unavailable)})
        for item in items:
            for tag in ('title', 'description', 'link'):
                self.assertTrue((item.findtext(tag) or '').strip(), tag)
            for tag in (
                'id',
                'price',
                'availability',
                'condition',
                'brand',
                'mpn',
                'product_type',
                'google_product_category',
                'image_link',
            ):
                self.assertTrue((_g(item, tag) or '').strip(), tag)
            self.assertIsNone(item.find(f'{{{G_NS}}}identifier_exists'))
            self.assertTrue(item.findtext('link').startswith(f'{base}/tovar/'))
            self.assertNotIn('/ru/', item.findtext('link'))
            self.assertIn(_g(item, 'availability'), {'in_stock', 'out_of_stock'})
            self.assertEqual(_g(item, 'condition'), 'new')
            self.assertEqual(_g(item, 'brand'), 'Rossa')
            self.assertEqual(_g(item, 'product_type'), 'Дивани > Кутові')
            self.assertEqual(_g(item, 'google_product_category'), '460')
            self.assertRegex(_g(item, 'price'), r'^\d+\.\d{2} UAH$')
            self.assertTrue(_g(item, 'id').startswith('rossa-'))
        active = self._by_product(items, self.active)
        self.assertEqual(active.findtext('title'), 'Мілан')
        self.assertEqual(active.findtext('link'), f'{base}/tovar/milan/')
        self.assertEqual(_g(active, 'id'), _pid(self.active))
        self.assertEqual(_g(active, 'mpn'), 'SOFA-1')
        self.assertEqual(_g(active, 'availability'), 'in_stock')
        missing = self._by_product(items, self.unavailable)
        self.assertEqual(_g(missing, 'availability'), 'out_of_stock')
        self.assertEqual(_g(missing, 'mpn'), 'SOFA-2')

    @override_settings(
        SITE_URL='https://merchant.example/',
        ALLOWED_HOSTS=['evil.invalid', 'testserver'],
    )
    def test_urls_use_site_url_not_request_host(self):
        response = self._response(HTTP_HOST='evil.invalid', secure=False)
        self.assertEqual(response.status_code, 200)
        self._assert_site_urls(response, foreign_host='evil.invalid')
        root, items = self._items(response)
        self.assertEqual(root.find('channel').findtext('link'), 'https://merchant.example/')
        active = self._by_product(items, self.active)
        self.assertEqual(active.findtext('link'), 'https://merchant.example/tovar/milan/')
        self.assertNotIn('merchant.example//', response.content.decode())

    def test_price_format(self):
        _, items = self._items(self._response())
        self.assertEqual(_g(self._by_product(items, self.active), 'price'), '1234.00 UAH')
        self.assertEqual(_g(self._by_product(items, self.unavailable), 'price'), '2500.00 UAH')

    def test_inactive_products_excluded(self):
        response = self._response()
        _, items = self._items(response)
        ids = {_g(item, 'id') for item in items}
        self.assertEqual(ids, {_pid(self.active), _pid(self.unavailable)})
        self.assertNotIn(_pid(self.hidden), ids)
        body = response.content.decode()
        self.assertNotIn('HIDDEN', body)
        self.assertNotIn('Прихований', body)
        self.assertNotIn('hidden-sofa', body)
        self.assertNotIn('не показувати', body)

    def test_description_html_is_stripped(self):
        response = self._response(HTTP_ACCEPT_LANGUAGE='ru')
        _, items = self._items(response)
        description = self._by_product(items, self.active).findtext('description')
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
        self._assert_site_urls(response)
        _, items = self._items(response)
        item = self._by_product(items, self.active)
        image = _g(item, 'image_link')
        base = settings.SITE_URL.rstrip('/')
        self.assertTrue(image.startswith(f'{base}/media/'))
        self.assertIn('main.webp', image)
        extra = item.findall(f'{{{G_NS}}}additional_image_link')
        self.assertEqual(len(extra), 1)
        self.assertTrue(extra[0].text.startswith(f'{base}/media/'))
        self.assertIn('extra.webp', extra[0].text)
        self.assertNotIn('secret-shade', response.content.decode())

    def test_skips_products_without_image_or_non_positive_price(self):
        no_image = Product.objects.create(
            slug='no-photo',
            sku='NO-PHOTO',
            name_uk='Без фото',
            category=self.active.category,
            base_price=1500,
            is_active=True,
        )
        free = _give_image(
            Product.objects.create(
                slug='free-sofa',
                sku='FREE',
                name_uk='Нульова ціна',
                category=self.active.category,
                base_price=0,
                is_active=True,
            ),
            'free.png',
        )
        fabric_free = _give_image(
            Product.objects.create(
                slug='fabric-free',
                sku='FAB0',
                name_uk='Тканина нуль',
                category=self.active.category,
                base_price=5000,
                is_active=True,
            ),
            'fab0.png',
        )
        fabric = Fabric.objects.create(slug='zero-fab', name_uk='Нуль')
        ProductFabricPrice.objects.create(product=fabric_free, fabric=fabric, price=0)
        response = self._response()
        _, items = self._items(response)
        ids = {_g(item, 'id') for item in items}
        self.assertEqual(ids, {_pid(self.active), _pid(self.unavailable)})
        for product in (no_image, free, fabric_free):
            self.assertNotIn(_pid(product), ids)
        body = response.content.decode()
        self.assertNotIn('Без фото', body)
        self.assertNotIn('Нульова ціна', body)
        self.assertNotIn('Тканина нуль', body)
        self.assertNotIn('NO-PHOTO', body)

    def test_mpn_or_identifier_exists(self):
        bare = _give_image(
            Product.objects.create(
                slug='no-sku',
                sku='   ',
                name_uk='Без артикула',
                category=self.active.category,
                base_price=1800,
                is_active=True,
            ),
            'bare.png',
        )
        _, items = self._items(self._response())
        with_sku = self._by_product(items, self.active)
        self.assertEqual(_g(with_sku, 'mpn'), 'SOFA-1')
        self.assertIsNone(with_sku.find(f'{{{G_NS}}}identifier_exists'))
        self.assertEqual(_g(with_sku, 'brand'), 'Rossa')
        without = self._by_product(items, bare)
        self.assertIsNone(without.find(f'{{{G_NS}}}mpn'))
        self.assertEqual(_g(without, 'identifier_exists'), 'no')
        self.assertEqual(_g(without, 'brand'), 'Rossa')
        self.assertEqual(_g(without, 'id'), _pid(bare))

    def test_google_product_category_in_feed(self):
        parent = Category.objects.get(slug='divany', parent__isnull=True)
        nested = _give_image(
            Product.objects.create(
                slug='nested-sofa',
                sku='NEST',
                name_uk='Нест',
                category=Category.objects.create(
                    slug='nestandart',
                    name_uk='Нестандарт',
                    parent=parent,
                ),
                base_price=3100,
                is_active=True,
            ),
            'nested.png',
        )
        table = _give_image(
            Product.objects.create(
                slug='oak-table',
                sku='TABLE',
                name_uk='Стіл',
                category=Category.objects.create(slug='stoly', name_uk='Столи'),
                base_price=2200,
                is_active=True,
            ),
            'table.png',
        )
        bed = _give_image(
            Product.objects.create(
                slug='bed-1',
                sku='BED',
                name_uk='Ліжко',
                category=Category.objects.create(slug='lizhka', name_uk='Ліжка'),
                base_price=8000,
                is_active=True,
            ),
            'bed.png',
        )
        pouf = _give_image(
            Product.objects.create(
                slug='pouf-1',
                sku='POUF',
                name_uk='Пуф',
                category=Category.objects.create(slug='pufy', name_uk='Пуфи'),
                base_price=900,
                is_active=True,
            ),
            'pouf.png',
        )
        _, items = self._items(self._response())
        expected = {
            self.active: '460',
            nested: '460',
            table: '436',
            bed: '505764',
            pouf: '458',
        }
        for product, category_id in expected.items():
            item = self._by_product(items, product)
            self.assertEqual(_g(item, 'google_product_category'), category_id, product.slug)

    def test_cache_invalidates_after_product_save(self):
        first = self._response()
        self.assertIn(b'1234.00 UAH', first.content)
        self.assertEqual(cache.get(FEED_CACHE_KEY), first.content)
        Product.objects.filter(pk=self.active.pk).update(base_price=6400)
        cached = self._response()
        self.assertEqual(cached.content, first.content)
        self.active.base_price = 6400
        self.active.save(update_fields=['base_price'])
        fresh = self._response()
        self.assertIn(b'6400.00 UAH', fresh.content)
        self.assertNotIn(b'1234.00 UAH', fresh.content)
        self.assertNotEqual(fresh.content, first.content)
        self.assertEqual(cache.get(FEED_CACHE_KEY), fresh.content)
        self.hidden.delete()
        self.assertIsNone(cache.get(FEED_CACHE_KEY))

    def test_related_model_signals_drop_feed_cache(self):
        self._response()
        self.active.category.name_uk = 'Кутові оновлені'
        self.active.category.save(update_fields=['name_uk'])
        self.assertIsNone(cache.get(FEED_CACHE_KEY))

        self._response()
        fabric = Fabric.objects.create(slug='wool', name_uk='Вовна')
        ProductFabricPrice.objects.create(product=self.active, fabric=fabric, price=2222)
        self.assertIsNone(cache.get(FEED_CACHE_KEY))
        priced = self._response()
        self.assertIn(b'2222.00 UAH', priced.content)

        option = ProductColorOption.objects.create(
            slug='olive',
            name_uk='Олива',
            hex_color='#556B2F',
        )
        color = ProductColor.objects.create(
            product=self.active,
            color=option,
            is_active=True,
        )
        self.assertIsNone(cache.get(FEED_CACHE_KEY))

        self._response()
        ProductColorImage.objects.create(
            product=self.active,
            color=option,
            image=_png('gallery.png'),
        )
        self.assertIsNone(cache.get(FEED_CACHE_KEY))

        self._response()
        color.delete()
        self.assertIsNone(cache.get(FEED_CACHE_KEY))
