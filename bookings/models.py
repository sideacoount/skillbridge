from django.conf import settings
from django.db import models


class Booking(models.Model):
    """A client request for a provider's service."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings_made'
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings_received'
    )
    service = models.ForeignKey('services.Service', on_delete=models.CASCADE, related_name='bookings')
    description = models.TextField(max_length=2000, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    preferred_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.client.username} → {self.service.title} ({self.get_status_display()})'
