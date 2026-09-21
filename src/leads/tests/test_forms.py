from django.test import Client, TestCase
from django.urls import reverse

from leads.models import ContactLead, OrderRequest, PartnershipLead


class LeadFormTests(TestCase):
    def setUp(self):
        from django.core.management import call_command
        call_command('seed_demo', verbosity=0)
        self.client = Client()

    def test_order_requires_phone(self):
        response = self.client.post(reverse('leads:order'), {
            'product_name': 'Мілан',
            'product_slug': 'milan',
            'fabric_name': 'Рогожка',
            'shade_name': 'Тауп',
            'price': 42900,
            'name': 'Іван',
            'phone': '',
            'consent': 'on',
            'fulfillment': 'pickup',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(OrderRequest.objects.count(), 0)

    def test_order_ok(self):
        response = self.client.post(reverse('leads:order'), {
            'product_name': 'Мілан',
            'product_slug': 'milan',
            'fabric_name': 'Рогожка',
            'shade_name': 'Тауп',
            'price': 42900,
            'name': 'Іван Петренко',
            'phone': '+380441234567',
            'consent': 'on',
            'fulfillment': 'pickup',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(OrderRequest.objects.count(), 1)

    def test_contact_ok(self):
        response = self.client.post(reverse('leads:contact'), {
            'name': 'Олена',
            'phone': '+380501112233',
            'message': 'Питання по дивану',
            'consent': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ContactLead.objects.count(), 1)

    def test_partnership_ok(self):
        response = self.client.post(reverse('leads:partnership'), {
            'company': 'Салон Тест',
            'phone': '+380671112233',
            'email': 'partner@example.com',
            'consent': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PartnershipLead.objects.count(), 1)
