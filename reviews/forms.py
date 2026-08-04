from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    """Write or edit a review with a star rating."""

    class Meta:
        model = Review
        fields = ('rating', 'comment', 'service')
        widgets = {
            'rating': forms.HiddenInput(attrs={'id': 'ratingValue'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Share your experience…', 'data-char-counter': 'review-comment',
            }),
            'service': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        provider = kwargs.pop('provider', None)
        client = kwargs.pop('client', None)
        super().__init__(*args, **kwargs)
        self.fields['rating'].initial = 5
        self.fields['service'].label = 'Service (optional)'
        if provider is not None and client is not None:
            from bookings.models import Booking
            done = Booking.objects.filter(client=client, provider=provider,
                                          status='completed').select_related('service')
            services = [b.service for b in done if b.service]
            self.fields['service'].queryset = self.fields['service'].queryset.filter(pk__in=[s.pk for s in services])
            if not services:
                self.fields.pop('service')

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None or not 1 <= rating <= 5:
            raise forms.ValidationError('Choose a rating between 1 and 5 stars.')
        return rating
