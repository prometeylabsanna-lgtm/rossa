"""Аудит CSP: enforce на vercel-профілі."""

from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    CONTENT_SECURITY_POLICY={
        'DIRECTIVES': {
            'default-src': ("'self'",),
            'script-src': ("'self'",),
            'object-src': ("'none'",),
            'frame-ancestors': ("'none'",),
        }
    },
    CONTENT_SECURITY_POLICY_REPORT_ONLY=None,
)
class CspEnforceTests(TestCase):
    def test_home_sends_csp_header(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        csp = response.get('Content-Security-Policy', '')
        self.assertIn("default-src 'self'", csp)
        self.assertIn("object-src 'none'", csp)
