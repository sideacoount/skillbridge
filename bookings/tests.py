from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Notification
from services.models import Category, Service
from .models import Booking

User = get_user_model()


class BookingTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Design', icon='bi-palette')
        self.provider = User.objects.create_user(
            username='dev', password='Passw0rd!', role=User.Role.STUDENT,
            is_provider_approved=True,
        )
        self.client_user = User.objects.create_user(
            username='client', password='Passw0rd!', role=User.Role.CLIENT,
        )
        self.service = Service.objects.create(
            provider=self.provider, category=self.category,
            title='Logo', description='d', price=50,
        )

    def test_client_can_create_booking(self):
        self.client.login(username='client', password='Passw0rd!')
        response = self.client.post(reverse('bookings:create', kwargs={'service_pk': self.service.pk}), {
            'preferred_date': '2026-12-01', 'budget': '60', 'description': 'Need a logo',
        })
        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.get(client=self.client_user, service=self.service)
        self.assertEqual(booking.status, Booking.Status.PENDING)
        # Provider should be notified
        self.assertTrue(Notification.objects.filter(user=self.provider, title='New booking request').exists())

    def test_provider_cannot_book_own_service(self):
        self.client.login(username='dev', password='Passw0rd!')
        response = self.client.post(reverse('bookings:create', kwargs={'service_pk': self.service.pk}), {
            'preferred_date': '2026-12-01', 'budget': '60',
        })
        self.assertEqual(Booking.objects.filter(service=self.service).count(), 0)
        self.assertEqual(response.status_code, 302)

    def test_provider_updates_status_and_client_cancels_pending(self):
        booking = Booking.objects.create(
            client=self.client_user, provider=self.provider,
            service=self.service, status='pending',
        )
        self.client.login(username='dev', password='Passw0rd!')
        self.client.post(reverse('bookings:update_status', kwargs={'pk': booking.pk}), {'status': 'accepted'})
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.ACCEPTED)
        # Accepted bookings cannot be cancelled by the client
        self.client.login(username='client', password='Passw0rd!')
        self.client.post(reverse('bookings:cancel', kwargs={'pk': booking.pk}))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.ACCEPTED)

        # A pending booking can be cancelled by the client
        pending = Booking.objects.create(
            client=self.client_user, provider=self.provider,
            service=self.service, status='pending',
        )
        self.client.post(reverse('bookings:cancel', kwargs={'pk': pending.pk}))
        pending.refresh_from_db()
        self.assertEqual(pending.status, Booking.Status.CANCELLED)

    def test_strangers_cannot_view_booking(self):
        other = User.objects.create_user(username='other', password='Passw0rd!', role=User.Role.CLIENT)
        booking = Booking.objects.create(
            client=self.client_user, provider=self.provider, service=self.service,
        )
        self.client.login(username='other', password='Passw0rd!')
        response = self.client.get(reverse('bookings:detail', kwargs={'pk': booking.pk}))
        self.assertEqual(response.status_code, 302)
