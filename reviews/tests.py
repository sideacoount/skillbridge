from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from bookings.models import Booking
from services.models import Category, Service
from .models import Review

User = get_user_model()


class ReviewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Dev', icon='bi-code')
        self.provider = User.objects.create_user(
            username='dev', password='Passw0rd!', role=User.Role.STUDENT,
            is_provider_approved=True,
        )
        self.client_user = User.objects.create_user(
            username='client', password='Passw0rd!', role=User.Role.CLIENT,
        )
        self.service = Service.objects.create(
            provider=self.provider, category=self.category,
            title='Site', description='d', price=100,
        )

    def test_review_requires_completed_booking(self):
        self.client.login(username='client', password='Passw0rd!')
        response = self.client.post(reverse('reviews:create', kwargs={'provider_pk': self.provider.pk}), {
            'rating': '5', 'comment': 'Great',
        })
        self.assertEqual(Review.objects.count(), 0)

    def test_review_after_completion_and_edit_delete(self):
        Booking.objects.create(
            client=self.client_user, provider=self.provider,
            service=self.service, status='completed',
        )
        self.client.login(username='client', password='Passw0rd!')
        self.client.post(reverse('reviews:create', kwargs={'provider_pk': self.provider.pk}), {
            'rating': '5', 'comment': 'Great work!',
        })
        review = Review.objects.get(client=self.client_user, provider=self.provider)
        self.assertEqual(review.rating, 5)

        self.client.post(reverse('reviews:edit', kwargs={'pk': review.pk}), {
            'rating': '4', 'comment': 'Edited',
        })
        review.refresh_from_db()
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Edited')

        self.client.post(reverse('reviews:delete', kwargs={'pk': review.pk}))
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

    def test_duplicate_review_redirects_to_edit(self):
        Review.objects.create(client=self.client_user, provider=self.provider, rating=5)
        Booking.objects.create(
            client=self.client_user, provider=self.provider,
            service=self.service, status='completed',
        )
        self.client.login(username='client', password='Passw0rd!')
        response = self.client.get(reverse('reviews:create', kwargs={'provider_pk': self.provider.pk}))
        self.assertEqual(response.status_code, 302)
