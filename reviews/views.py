from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.models import Notification, User
from bookings.models import Booking
from services.models import Service

from .models import Review
from .forms import ReviewForm


def _notify(user, title, message, link):
    Notification.objects.create(user=user, title=title, message=message, link=link)


@login_required
def create_review(request, provider_pk):
    """Client writes a review for a provider they've completed work with."""
    provider = get_object_or_404(User, pk=provider_pk)
    if provider == request.user:
        messages.error(request, 'You cannot review yourself.')
        return redirect('dashboard:home')

    done = Booking.objects.filter(client=request.user, provider=provider, status='completed').exists()
    if not done:
        messages.error(request, 'You can only review a provider after a completed booking.')
        return redirect('accounts:public_profile', username=provider.username)

    existing = Review.objects.filter(client=request.user, provider=provider).first()
    if existing:
        messages.info(request, 'You already reviewed this provider. Editing your review.')
        return redirect('reviews:edit', pk=existing.pk)

    form = ReviewForm(request.POST or None, provider=provider, client=request.user)
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.client = request.user
        review.provider = provider
        review.save()
        _notify(provider, 'New review',
                f'{request.user.username} left you a {review.rating}★ review.',
                reverse('accounts:public_profile', kwargs={'username': provider.username}))
        messages.success(request, 'Thanks! Your review has been published.')
        return redirect('accounts:public_profile', username=provider.username)

    return render(request, 'reviews/review_form.html', {'form': form, 'provider': provider, 'title': 'Write a review'})


@login_required
def edit_review(request, pk):
    review = get_object_or_404(Review, pk=pk, client=request.user)
    form = ReviewForm(request.POST or None, instance=review, provider=review.provider, client=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Review updated.')
        return redirect('accounts:public_profile', username=review.provider.username)
    return render(request, 'reviews/review_form.html', {'form': form, 'provider': review.provider, 'title': 'Edit review'})


@login_required
@require_POST
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.user != review.client and not request.user.is_superuser:
        messages.error(request, 'You can only delete your own reviews.')
        return redirect('accounts:public_profile', username=review.provider.username)
    username = review.provider.username
    review.delete()
    messages.success(request, 'Review deleted.')
    return redirect('accounts:public_profile', username=username)
