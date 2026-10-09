"""Admin/CMS: sanitize на save + HEX валідація."""

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase

from catalog.models import ProductColorOption
from core.cms_text import ensure_cms_html


class AdminCmsSanitizeTests(SimpleTestCase):
    def test_ensure_cms_html_strips_script_on_save_path(self):
        out = ensure_cms_html('<p>ok</p><script>alert(1)</script>')
        self.assertIn('<p>ok</p>', out)
        self.assertNotIn('<script>', out)

    def test_ensure_cms_html_strips_handlers(self):
        out = ensure_cms_html('<p onmouseover="alert(1)">x</p>')
        self.assertEqual(out, '<p>x</p>')


class HexColorValidationTests(TestCase):
    def test_rejects_css_injection(self):
        opt = ProductColorOption(
            slug='evil',
            name_uk='Evil',
            hex_color='red;"><img src=x onerror=alert(1)>',
        )
        with self.assertRaises(ValidationError):
            opt.full_clean()

    def test_accepts_valid_hex(self):
        opt = ProductColorOption(
            slug='beige-test',
            name_uk='Беж',
            hex_color='#D4C4A8',
        )
        opt.full_clean()
