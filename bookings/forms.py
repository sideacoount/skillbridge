from django import forms

from .models import Booking


class BookingForm(forms.ModelForm):
    """Client-facing booking request form."""

    class Meta:
        model = Booking
        fields = ('preferred_date', 'budget', 'description')
        widgets = {
            'preferred_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
            ),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': 'Your budget', 'min': '0', 'step': '0.01',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Describe your project, goals and timeline…',
            }),
        }

    def clean_preferred_date(self):
        from django.utils import timezone
        date = self.cleaned_data.get('preferred_date')
        if date and date < timezone.now().date():
            raise forms.ValidationError('Preferred date cannot be in the past.')
        return date
