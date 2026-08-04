from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with roles for the SkillBridge marketplace."""

    class Role(models.TextChoices):
        STUDENT = 'student', 'Student / Provider'
        CLIENT = 'client', 'Client'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(max_length=1000, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    occupation = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    skills = models.ManyToManyField('services.Category', related_name='providers', blank=True)
    is_provider_approved = models.BooleanField(
        default=False,
        help_text='Approved by admin before a student can publish services.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def average_rating(self):
        from reviews.models import Review
        agg = Review.objects.filter(provider=self).aggregate(
            avg=models.Avg('rating'), count=models.Count('id')
        )
        return agg['avg'] or 0, agg['count'] or 0

    @property
    def completed_jobs(self):
        return self.bookings_received.filter(status='completed').count()

    def profile_completion(self):
        """Returns an integer 0-100 describing profile completeness."""
        score = 0
        fields = [self.first_name, self.last_name, self.bio, self.phone]
        score += sum(1 for f in fields if f) * 15
        score += 10 if self.profile_image else 0
        score += 10 if self.location else 0
        score += 10 if self.occupation else 0
        if self.is_student:
            score += 10 if self.services.count() else 0
        else:
            score = min(score, 90)
            score += 10
        return min(score, 100)

    def unread_notifications(self):
        return self.notifications.filter(is_read=False).count()

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'


class Notification(models.Model):
    """In-app notification shown in the bell dropdown."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=120)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.title}'
