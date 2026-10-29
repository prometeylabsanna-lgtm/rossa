"""Google Tag Manager: лише після згоди на cookies (client-side)."""

import re

from csp.constants import NONCE
from django.test import TestCase, override_settings
from django.urls import reverse

GTM_ID = 'GTM-NZN8FDT7'
GTM_JS = 'https://www.googletagmanager.com/gtm.js'


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

    def test_gtm_not_autoinjected_without_consent(self):
        response, html = self._page()
        self.assertNotIn(GTM_JS, html)
        self.assertNotIn('ns.html', html)
        self.assertContains(response, 'data-cookie-banner')
        self.assertContains(response, f'data-gtm-id="{GTM_ID}"')
        self.assertContains(response, 'js/cookie-consent.js')

    def test_cookie_banner_actions_present(self):
        response, _html = self._page()
        self.assertContains(response, 'data-cookie-accept')
        self.assertContains(response, 'data-cookie-necessary')
        self.assertContains(response, reverse('core:cookies'))

    @override_settings(GTM_ID="');alert(1);//")
    def test_absent_when_gtm_id_is_not_a_container_id(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        banner = re.search(r'data-gtm-id="([^"]*)"', html)
        self.assertIsNotNone(banner)
        self.assertEqual(banner.group(1), '')
        self.assertNotContains(response, 'alert(1)')

    @override_settings(GTM_ID='')
    def test_absent_when_gtm_id_empty(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('data-gtm-id=""', html)
        self.assertNotIn(GTM_JS, html)
        self.assertNotIn('ns.html', html)

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
    def test_cookie_consent_script_without_inline_gtm(self):
        response, html = self._page()
        self.assertEqual(response.status_code, 200)
        self.assertIn('js/cookie-consent.js', html)
        self.assertNotIn(GTM_JS, html)
        self.assertIn(f'data-gtm-id="{GTM_ID}"', html)
