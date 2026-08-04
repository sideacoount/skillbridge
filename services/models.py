from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """A service category shown in the browse/filter bar."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icon = models.CharField(
        max_length=60, default='bi-box',
        help_text='Bootstrap Icons class, e.g. bi-code-slash',
    )
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Service(models.Model):
    """A service listing created by an approved student provider."""

    class Availability(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        BUSY = 'busy', 'Busy'
        LIMITED = 'limited', 'Limited slots'

    title = models.CharField(max_length=160)
    description = models.TextField(max_length=3000)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='services')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    availability = models.CharField(
        max_length=20, choices=Availability.choices, default=Availability.AVAILABLE
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='services'
    )
    is_approved = models.BooleanField(
        default=True,
        help_text='Admin approval gate; false hides the listing.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('services:detail', kwargs={'pk': self.pk})

    @property
    def average_rating(self):
        return self.provider.average_rating

    @property
    def review_count(self):
        return self.provider.average_rating[1]

    @property
    def is_booked_by(self, user):
        from bookings.models import Booking
        return Booking.objects.filter(service=self, client=user).exists()


class Wishlist(models.Model):
    """A saved service the user wants to remember or book later."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'service')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} → {self.service.title}'
