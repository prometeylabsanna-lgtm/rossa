"""Санітизація CMS HTML (stored XSS)."""

from django.template import Context, Template
from django.test import SimpleTestCase

from core.cms_sanitize import sanitize_cms_html


class CmsSanitizeTests(SimpleTestCase):
    def test_strips_script(self):
        html = sanitize_cms_html('<p>ok</p><script>alert(1)</script>')
        self.assertIn('<p>ok</p>', html)
        self.assertNotIn('<script>', html)
        self.assertNotIn('</script>', html)

    def test_strips_event_handlers(self):
        html = sanitize_cms_html('<p onclick="alert(1)">текст</p>')
        self.assertEqual(html, '<p>текст</p>')

    def test_blocks_javascript_href(self):
        html = sanitize_cms_html('<a href="javascript:alert(1)">x</a>')
        self.assertNotIn('javascript:', html)

    def test_keeps_safe_markup(self):
        src = '<p>Привіт <strong>ROSSA</strong></p><ul><li>a</li></ul>'
        self.assertEqual(sanitize_cms_html(src), src)

    def test_blank_target_gets_noopener(self):
        html = sanitize_cms_html('<a href="https://rossa.ua" target="_blank">сайт</a>')
        self.assertIn('rel="noopener noreferrer"', html)
        self.assertIn('href="https://rossa.ua"', html)

    def test_filter_cms_html_escapes_payload(self):
        tpl = Template('{% load rossa %}{{ body|cms_html }}')
        out = tpl.render(Context({'body': '<img src=x onerror=alert(1)><p>safe</p>'}))
        self.assertNotIn('onerror', out)
        self.assertNotIn('<img', out)
        self.assertIn('<p>safe</p>', out)
