"""Google Tag Manager на публічних сторінках."""

import re

from csp.constants import NONCE
from django.test import TestCase, override_settings
from django.urls import reverse

GTM_ID = 'GTM-NZN8FDT7'
GTM_JS = 'https://www.googletagmanager.com/gtm.js'
GTM_NS = f'https://www.googletagmanager.com/ns.html?id={GTM_ID}'


def _csp_header(response) -> str:
    enforced = response.get('Content-Security-Policy', '')
    report_only = response.get('Content-Security-Policy-Report-Only', '')
    return enforced or report_only


def _directive(csp: str, name: str) -> str:
    prefix = f'{name} '
    for part in csp.split(';'):
        part = part.strip()
        if part.startswith(prefix):
            return part
    return ''


@override_settings(GTM_ID=GTM_ID)
class GoogleTagManagerTests(TestCase):
    def _page(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        return response, response.content.decode()

    def test_head_script_and_noscript_after_body(self):
        response, html = self._page()
        head, _, after_head = html.partition('</head>')
        head_inner = head.split('<head>', 1)[1].lstrip()
        self.assertTrue(head_inner.startswith('<script'), head_inner[:120])
        script = head_inner.split('</script>', 1)[0]
        self.assertIn(GTM_JS, script)
        self.assertIn(GTM_ID, script)
        self.assertNotIn('ns.html', head)
        self.assertRegex(
            after_head,
            r'<body\b[^>]*>\s*<noscript><iframe src="' + re.escape(GTM_NS),
        )
        self.assertContains(response, GTM_NS)

    @override_settings(GTM_ID="');alert(1);//")
    def test_absent_when_gtm_id_is_not_a_container_id(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'googletagmanager.com')
        self.assertNotContains(response, 'alert(1)')

    @override_settings(GTM_ID='')
    def test_absent_when_gtm_id_empty(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'googletagmanager.com')
        self.assertNotContains(response, 'gtm.js')
        self.assertNotContains(response, 'ns.html')

    def test_csp_header_contains_googletagmanager(self):
        response, _html = self._page()
        csp = _csp_header(response)
        self.assertIn('https://www.googletagmanager.com', csp)
        for name in ('script-src', 'img-src', 'frame-src', 'connect-src'):
            self.assertIn(
                'https://www.googletagmanager.com',
                _directive(csp, name),
                name,
            )
        for name in ('img-src', 'connect-src'):
            directive = _directive(csp, name)
            self.assertIn('https://www.google-analytics.com', directive, name)
            self.assertIn('https://*.google-analytics.com', directive, name)

    @override_settings(
        CONTENT_SECURITY_POLICY={
            'DIRECTIVES': {
                'default-src': ("'self'",),
                'script-src': ("'self'", NONCE),
            }
        },
        CONTENT_SECURITY_POLICY_REPORT_ONLY=None,
    )
    def test_script_nonce_when_csp_uses_nonces(self):
        response, html = self._page()
        csp = response['Content-Security-Policy']
        match = re.search(r"'nonce-([^']+)'", csp)
        self.assertIsNotNone(match)
        nonce = match.group(1)
        head = html.split('</head>', 1)[0]
        self.assertIn(f'<script nonce="{nonce}">', head)
        self.assertIn(GTM_JS, head)
