from django.test import SimpleTestCase, TestCase

from catalog.models import Category, Product
from core.slug import make_slug


class SlugUtilsTests(SimpleTestCase):
    def test_make_slug_uk(self):
        self.assertEqual(make_slug('Дивани'), 'dyvany')
        self.assertEqual(make_slug('Мілан'), 'milan')
        self.assertEqual(make_slug('Ліжка'), 'lizhka')


class AutoSlugModelTests(TestCase):
    def test_product_slug_from_name_and_regen(self):
        cat = Category.objects.create(name_uk='Тест кат', name_ru='Тест')
        self.assertEqual(cat.slug, 'test-kat')
        product = Product.objects.create(
            name_uk='Альфа',
            name_ru='Альфа',
            category=cat,
            base_price=1000,
        )
        self.assertEqual(product.slug, 'alfa')
        product.name_uk = 'Бета'
        product.save()
        product.refresh_from_db()
        self.assertEqual(product.slug, 'beta')

    def test_category_unique_per_parent(self):
        root = Category.objects.create(name_uk='Корінь', name_ru='Корень')
        a = Category.objects.create(name_uk='Під', name_ru='Под', parent=root)
        b = Category.objects.create(name_uk='Під', name_ru='Под', parent=root)
        self.assertEqual(a.slug, 'pid')
        self.assertEqual(b.slug, 'pid-2')
