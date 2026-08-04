from django import forms

from .models import Service, Category


class ServiceForm(forms.ModelForm):
    """Create / edit a service listing."""

    class Meta:
        model = Service
        fields = ('title', 'category', 'description', 'price', 'availability', 'image')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. Modern website design in 48h',
                'data-char-counter': 'title', 'maxlength': '160',
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 6,
                'placeholder': 'Describe what you deliver, timelines and revisions…',
                'data-char-counter': 'description', 'maxlength': '3000',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control', 'placeholder': '49.99', 'min': '0', 'step': '0.01',
            }),
            'availability': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control', 'accept': 'image/*', 'data-image-preview': 'serviceImagePreview',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = 'Choose a category…'

    def clean_price(self):
        price = self.cleaned_data['price']
        if price is not None and price <= 0:
            raise forms.ValidationError('Price must be greater than zero.')
        return price


class ServiceFilterForm(forms.Form):
    """Filters used on the browse page."""

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), required=False, empty_label='All categories',
        widget=forms.Select(attrs={'class': 'form-select filter-select'}),
    )
    min_price = forms.DecimalField(
        required=False, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min price'}),
    )
    max_price = forms.DecimalField(
        required=False, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max price'}),
    )
    availability = forms.ChoiceField(
        choices=[('', 'Any availability')] + list(Service.Availability.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    min_rating = forms.ChoiceField(
        choices=[('', 'Any rating'), ('4', '4+ stars'), ('3', '3+ stars'),
                 ('2', '2+ stars'), ('1', '1+ stars')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    sort = forms.ChoiceField(
        choices=[('newest', 'Newest'), ('price_low', 'Price: Low to High'),
                 ('price_high', 'Price: High to Low'), ('rating', 'Top rated'),
                 ('popular', 'Most booked')],
        required=False, initial='newest',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
