from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator

from .models import User


class RoleChoiceField(forms.TypedChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', forms.Select(attrs={'class': 'form-select'}))
        super().__init__(*args, **kwargs)


class RegisterForm(UserCreationForm):
    """Custom registration with role selection and profile basics."""

    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@email.com'}),
    )
    phone = forms.CharField(
        required=False,
        max_length=20,
        validators=[RegexValidator(r'^\+?[0-9 ]{7,20}$', 'Enter a valid phone number.')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 890'}),
    )
    role = RoleChoiceField(
        choices=User.Role.choices,
        initial=User.Role.CLIENT,
        help_text='Choose how you want to use SkillBridge.',
    )
    bio = forms.CharField(
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3,
            'placeholder': 'Tell clients a little about yourself…',
        }),
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'phone',
                  'role', 'bio', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.setdefault('class', 'form-control')
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Choose a username',
        })
        self.fields['username'].help_text = '150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['password1'].widget.attrs.update({'placeholder': 'Create a password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm your password'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = user.email.lower()
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username or email'}),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Your password'}),
    )


class ProfileForm(forms.ModelForm):
    """Editable profile fields."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'bio',
                  'occupation', 'location', 'website', 'profile_image')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@email.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 890'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell clients about yourself…', 'data-char-counter': 'bio'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Freelance Web Developer'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Nairobi, Kenya'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://your-portfolio.com'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'data-image-preview': 'profileImagePreview'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is already registered.')
        return email


class SkillsForm(forms.ModelForm):
    """Edit which skill categories a provider offers."""

    class Meta:
        model = User
        fields = ('skills',)
        widgets = {
            'skills': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }
