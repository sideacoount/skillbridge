from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Notification

User = get_user_model()


class AccountAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='client', email='client@example.com', password='Passw0rd!',
            first_name='Cee', role=User.Role.CLIENT,
        )

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'New', 'last_name': 'Guy', 'username': 'newguy',
            'email': 'newguy@example.com', 'role': 'student',
            'password1': 'Str0ngPass!', 'password2': 'Str0ngPass!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newguy').exists())

    def test_login_with_email(self):
        ok = self.client.login(username='client@example.com', password='Passw0rd!')
        self.assertTrue(ok)

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)

    def test_unread_notification_count(self):
        Notification.objects.create(user=self.user, title='Hi', message='Test')
        self.assertEqual(self.user.unread_notifications(), 1)


class PasswordResetTests(TestCase):
    def setUp(self):
        User.objects.create_user(username='u', email='u@example.com', password='Passw0rd!')

    def test_reset_request_redirects_to_login(self):
        response = self.client.post(reverse('accounts:password_reset'), {'email': 'u@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:login'))

    def test_invalid_token_is_rejected(self):
        response = self.client.post(
            reverse('accounts:password_reset_confirm', kwargs={'uidb64': 'zz', 'token': 'bad'})
        )
        self.assertEqual(response.status_code, 302)
