"""Юніт-перевірки фіда: ціна, URL, таксономія Google."""
from decimal import Decimal

from django.test import SimpleTestCase, override_settings

from catalog.google_feed import (
    DEFAULT_GOOGLE_PRODUCT_CATEGORY,
    GOOGLE_PRODUCT_CATEGORY_BY_SLUG,
    absolute_url,
    cap_image_urls,
    format_price_uah,
    google_product_category_id,
)


class _Cat:
    def __init__(self, slug, parent=None, pk=1):
        self.slug = slug
        self.parent = parent
        self.pk = pk


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


class GoogleFeedPriceTests(SimpleTestCase):
    def test_quantize_keeps_fractional_cents(self):
        self.assertEqual(format_price_uah(Decimal('1234.567')), '1234.57 UAH')
        self.assertEqual(format_price_uah(Decimal('10.9')), '10.90 UAH')
        self.assertEqual(format_price_uah(1999), '1999.00 UAH')
        self.assertEqual(format_price_uah(Decimal('1.005')), '1.01 UAH')


class GoogleFeedUrlTests(SimpleTestCase):
    @override_settings(SITE_URL='https://rossamebel.com.ua/')
    def test_relative_and_absolute_media(self):
        self.assertEqual(
            absolute_url('/media/products/a.webp'),
            'https://rossamebel.com.ua/media/products/a.webp',
        )
        self.assertEqual(
            absolute_url('media/products/a.webp'),
            'https://rossamebel.com.ua/media/products/a.webp',
        )
        self.assertEqual(absolute_url('/'), 'https://rossamebel.com.ua/')
        self.assertEqual(
            absolute_url('https://cdn.example/a.webp'),
            'https://cdn.example/a.webp',
        )
        self.assertEqual(
            absolute_url('http://cdn.example/a.webp'),
            'http://cdn.example/a.webp',
        )


class GoogleFeedCategoryMapTests(SimpleTestCase):
    def test_slug_ids(self):
        self.assertEqual(
            GOOGLE_PRODUCT_CATEGORY_BY_SLUG,
            {
                'divany': '460',
                'modulni': '460',
                'kutovi': '460',
                'pryami': '460',
                'yevroknyzhky': '460',
                'lizhka': '505764',
                'pufy': '458',
            },
        )
        self.assertEqual(DEFAULT_GOOGLE_PRODUCT_CATEGORY, '436')

    def test_parent_walk_and_default(self):
        parent = _Cat('divany', pk=1)
        self.assertEqual(google_product_category_id(_Cat('nestandart', parent, pk=2)), '460')
        self.assertEqual(google_product_category_id(_Cat('kutovi', parent, pk=3)), '460')
        self.assertEqual(google_product_category_id(_Cat('stoly', pk=4)), '436')
        self.assertEqual(google_product_category_id(_Cat('lizhka', pk=5)), '505764')
        self.assertEqual(google_product_category_id(_Cat('pufy', pk=6)), '458')
        self.assertEqual(google_product_category_id(None), '436')
