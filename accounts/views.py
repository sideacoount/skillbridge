from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.http import require_POST
from django.views.generic import FormView, CreateView

from .forms import RegisterForm, LoginForm, ProfileForm, SkillsForm
from .models import User, Notification


def register(request):
    """Create a new account and log the user in."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(
            request,
            f'Welcome to SkillBridge, {user.first_name or user.username}! '
            'Complete your profile to get started.',
        )
        return redirect('dashboard:home')
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Log a user in (username or email accepted)."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Welcome back, {user.first_name or user.username}!')
        next_url = request.GET.get('next')
        return redirect(next_url or 'dashboard:home')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out. See you soon!')
    return redirect('services:home')


def password_reset(request):
    """Simple password reset that emails a reset link (console backend in dev)."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        user = User.objects.filter(email=email).first()
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            site = get_current_site(request)
            reset_url = request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            subject = 'Reset your SkillBridge password'
            body = render_to_string('accounts/emails/password_reset.txt', {
                'user': user, 'reset_url': reset_url, 'site': site.domain,
            })
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])
        # Always show success to avoid leaking which emails exist.
        messages.success(request, 'If that email is registered, a reset link is on its way.')
        return redirect('accounts:login')
    return render(request, 'accounts/password_reset.html')


def password_reset_confirm(request, uidb64, token):
    """Confirm a password reset link and set a new password."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, 'This reset link is invalid or has expired.')
        return redirect('accounts:password_reset')
    if request.method == 'POST':
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        elif password != password2:
            messages.error(request, 'Passwords do not match.')
        else:
            user.set_password(password)
            user.save()
            messages.success(request, 'Password updated. You can now log in.')
            return redirect('accounts:login')
    return render(request, 'accounts/password_reset_confirm.html', {'validlink': True})


@login_required
def profile(request, username=None):
    """View a public profile, optionally that of another user."""
    target = get_object_or_404(User, username=username) if username else request.user
    from reviews.models import Review
    avg_rating, review_count = target.average_rating
    context = {
        'target': target,
        'own_profile': target == request.user,
        'avg_rating': avg_rating,
        'review_count': review_count,
        'reviews': Review.objects.filter(provider=target).select_related('client')[:6],
        'services': target.services.filter(is_approved=True) if target.is_student else [],
        'completion': target.profile_completion() if target == request.user else None,
        'completion_checks': ([
            {'label': 'First & last name', 'done': bool(target.first_name and target.last_name)},
            {'label': 'Bio', 'done': bool(target.bio)},
            {'label': 'Profile photo', 'done': bool(target.profile_image)},
            {'label': 'Phone number', 'done': bool(target.phone)},
            {'label': 'Location', 'done': bool(target.location)},
            {'label': 'Occupation', 'done': bool(target.occupation)},
        ] if target == request.user else []),
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your profile has been updated.')
        return redirect('accounts:profile')
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
@require_POST
def set_role(request):
    """Switch between student and client role from the dashboard."""
    role = request.POST.get('role')
    if role in User.Role.values:
        request.user.role = role
        request.user.save()
        messages.success(request, 'Your role is now a ' + request.user.get_role_display() + '.')
    return redirect('dashboard:home')


@login_required
def notifications(request):
    notifications_ = request.user.notifications.all()
    return render(request, 'accounts/notifications.html', {'notifications_list': notifications_})


@login_required
@require_POST
def mark_notifications_read(request):
    request.user.notifications.update(is_read=True)
    return JsonResponse({'ok': True})
