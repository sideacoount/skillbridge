from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.models import Notification
from services.models import Service

from .models import Booking
from .forms import BookingForm

VALID_STATUSES = Booking.Status.values


def _notify(user, title, message, link):
    Notification.objects.create(user=user, title=title, message=message, link=link)


@login_required
def create_booking(request, service_pk):
    """Client creates a booking request for a service."""
    service = get_object_or_404(Service.objects.select_related('provider'), pk=service_pk)

    if service.provider == request.user:
        messages.error(request, 'You cannot book your own service.')
        return redirect('services:detail', pk=service.pk)
    if not service.is_approved:
        messages.error(request, 'This service is not available.')
        return redirect('services:browse')

    existing = Booking.objects.filter(service=service, client=request.user, status='pending').first()
    if existing:
        messages.info(request, 'You already have a pending booking for this service.')
        return redirect('bookings:detail', pk=existing.pk)

    form = BookingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        booking = form.save(commit=False)
        booking.client = request.user
        booking.provider = service.provider
        booking.service = service
        booking.save()
        _notify(
            service.provider,
            'New booking request',
            f'{request.user.get_full_name() or request.user.username} booked “{service.title}”.',
            reverse('bookings:detail', kwargs={'pk': booking.pk}),
        )
        messages.success(request, 'Booking request sent! The provider has been notified.')
        return redirect('bookings:detail', pk=booking.pk)

    return render(request, 'bookings/booking_form.html', {
        'form': form, 'service': service,
    })


@login_required
def my_bookings(request):
    """Client's booking history."""
    bookings = Booking.objects.filter(client=request.user).select_related('service', 'service__provider')
    return render(request, 'bookings/my_bookings.html', {'bookings': bookings})


@login_required
def incoming_bookings(request):
    """Provider's received booking requests."""
    bookings = Booking.objects.filter(provider=request.user).select_related('client', 'service')
    return render(request, 'bookings/incoming_bookings.html', {'bookings': bookings})


@login_required
def booking_detail(request, pk):
    """Booking detail page visible to the involved client or provider."""
    booking = get_object_or_404(
        Booking.objects.select_related('client', 'provider', 'service', 'service__provider'),
        pk=pk,
    )
    if request.user not in (booking.client, booking.provider):
        messages.error(request, 'You do not have access to this booking.')
        return redirect('dashboard:home')
    is_provider = request.user == booking.provider
    return render(request, 'bookings/booking_detail.html', {
        'booking': booking, 'is_provider': is_provider,
    })


@login_required
@require_POST
def update_status(request, pk):
    """Provider updates booking status (accept / complete / cancel)."""
    booking = get_object_or_404(Booking, pk=pk, provider=request.user)
    new_status = request.POST.get('status')
    if new_status not in VALID_STATUSES:
        messages.error(request, 'Invalid status.')
        return redirect('bookings:detail', pk=pk)
    if new_status == 'accepted' and booking.status == 'pending':
        _notify(booking.client, 'Booking accepted',
                f'{request.user.username} accepted your booking for “{booking.service.title}”.',
                reverse('bookings:detail', kwargs={'pk': booking.pk}))
    elif new_status == 'cancelled':
        _notify(booking.client, 'Booking cancelled',
                f'{request.user.username} cancelled the booking for “{booking.service.title}”.',
                reverse('bookings:detail', kwargs={'pk': booking.pk}))
    elif new_status == 'completed':
        _notify(booking.client, 'Booking completed 🎉',
                f'“{booking.service.title}” is marked complete. Review your provider!',
                reverse('reviews:create', kwargs={'provider_pk': booking.provider_id}))
    booking.status = new_status
    booking.save()
    messages.success(request, f'Booking marked as {booking.get_status_display()}.')
    return redirect('bookings:detail', pk=pk)


@login_required
@require_POST
def cancel_booking(request, pk):
    """Client cancels a pending booking."""
    booking = get_object_or_404(Booking, pk=pk, client=request.user)
    if booking.status != 'pending':
        messages.error(request, 'Only pending bookings can be cancelled.')
        return redirect('bookings:detail', pk=pk)
    booking.status = 'cancelled'
    booking.save()
    _notify(booking.provider, 'Booking cancelled',
            f'{request.user.username} cancelled the booking for “{booking.service.title}”.',
            reverse('bookings:detail', kwargs={'pk': booking.pk}))
    messages.success(request, 'Booking cancelled.')
    return redirect('bookings:my_bookings')


@login_required
@require_POST
def delete_booking(request, pk):
    """Provider deletes a booking record entirely."""
    booking = get_object_or_404(Booking, pk=pk, provider=request.user)
    booking.delete()
    messages.success(request, 'Booking deleted.')
    return redirect('bookings:incoming')
