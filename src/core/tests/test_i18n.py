from django.test import SimpleTestCase

from core.utils import localized


class Obj:
    title_uk = 'Привіт'
    title_ru = ''


class LocalizedTests(SimpleTestCase):
    def test_fallback_uk(self):
        self.assertEqual(localized(Obj(), 'title', 'ru'), 'Привіт')
        self.assertEqual(localized(Obj(), 'title', 'uk'), 'Привіт')
