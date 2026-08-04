from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Service, Wishlist

User = get_user_model()


class ServiceTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Web Dev', icon='bi-code-slash')
        self.provider = User.objects.create_user(
            username='dev', password='Passw0rd!', role=User.Role.STUDENT,
            is_provider_approved=True,
        )
        self.client_user = User.objects.create_user(
            username='client', password='Passw0rd!', role=User.Role.CLIENT,
        )
        self.service = Service.objects.create(
            provider=self.provider, category=self.category,
            title='Landing page', description='A nice page',
            price=99, availability='available',
        )

    def test_home_and_browse_load(self):
        self.assertEqual(self.client.get(reverse('services:home')).status_code, 200)
        self.assertEqual(self.client.get(reverse('services:browse')).status_code, 200)

    def test_search_api_returns_service(self):
        response = self.client.get(reverse('services:search_api'), {'q': 'landing'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Landing page', response.json()['html'])

    def test_unapproved_service_hidden_from_public(self):
        self.service.is_approved = False
        self.service.save()
        response = self.client.get(reverse('services:detail', kwargs={'pk': self.service.pk}))
        self.assertEqual(response.status_code, 404)

    def test_non_approved_provider_cannot_create(self):
        self.client.login(username='client', password='Passw0rd!')
        response = self.client.post(reverse('services:create'), {
            'title': 'X', 'category': self.category.pk,
            'description': 'd', 'price': '10', 'availability': 'available',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Service.objects.filter(title='X').count(), 0)

    def test_provider_crud(self):
        self.client.login(username='dev', password='Passw0rd!')
        created = self.client.post(reverse('services:create'), {
            'title': 'New gig', 'category': self.category.pk,
            'description': 'desc', 'price': '50', 'availability': 'available',
        })
        self.assertEqual(created.status_code, 302)
        service = Service.objects.get(title='New gig')
        self.client.post(reverse('services:update', kwargs={'pk': service.pk}), {
            'title': 'Updated gig', 'category': self.category.pk,
            'description': 'desc', 'price': '60', 'availability': 'limited',
        })
        service.refresh_from_db()
        self.assertEqual(service.title, 'Updated gig')
        self.client.post(reverse('services:delete', kwargs={'pk': service.pk}))
        self.assertFalse(Service.objects.filter(pk=service.pk).exists())

    def test_wishlist_toggle(self):
        self.client.login(username='client', password='Passw0rd!')
        self.client.post(reverse('services:toggle_wishlist', kwargs={'pk': self.service.pk}))
        self.assertTrue(Wishlist.objects.filter(user=self.client_user, service=self.service).exists())
        self.client.post(reverse('services:toggle_wishlist', kwargs={'pk': self.service.pk}))
        self.assertFalse(Wishlist.objects.filter(user=self.client_user, service=self.service).exists())
