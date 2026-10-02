from django.test import Client, TestCase
from django.urls import reverse

CREDIT_URL = 'https://www.prometeylabs.com/internet-shop-v2/'


class FooterDeveloperLinkTests(TestCase):
    def setUp(self):
        from django.core.management import call_command

        call_command('seed_demo', verbosity=0)
        self.client = Client()

    def test_home_has_nofollow_credit_link(self):
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, CREDIT_URL)
        self.assertContains(response, 'nofollow')
        self.assertContains(response, '>PrometeyLabs</a>')
        self.assertContains(response, 'site-footer__credit-link')

    def test_inner_pages_show_credit_without_link(self):
        for name in ('core:about', 'core:privacy', 'core:contacts'):
            response = self.client.get(reverse(name))
            self.assertContains(response, 'PrometeyLabs', msg_prefix=name)
            self.assertNotContains(response, CREDIT_URL, msg_prefix=name)
            self.assertNotContains(response, 'site-footer__credit-link', msg_prefix=name)
