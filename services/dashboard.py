from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum, Q
from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta

from bookings.models import Booking
from reviews.models import Review
from .models import Service


@login_required
def home(request):
    """Role-aware dashboard with analytics, charts and quick actions."""
    user = request.user
    context = {'is_student': user.is_student, 'is_client': user.is_client}
    context['completion'] = user.profile_completion()

    # Client + provider shared stats
    context['total_bookings'] = Booking.objects.filter(client=user).count()
    context['pending_bookings'] = Booking.objects.filter(client=user, status='pending').count()
    context['cancelled_bookings'] = Booking.objects.filter(client=user, status='cancelled').count()
    context['client_spend'] = Booking.objects.filter(client=user).aggregate(
        total=Sum('service__price'))['total'] or 0

    # Provider-only analytics
    if user.is_student:
        service_qs = Service.objects.filter(provider=user)
        incoming = Booking.objects.filter(provider=user)
        context['my_services_count'] = service_qs.count()
        context['incoming_bookings'] = incoming.count()
        context['completed_jobs'] = incoming.filter(status='completed').count()
        context['accepted_pending'] = incoming.filter(status__in=['pending', 'accepted']).count()
        avg, _ = user.average_rating
        context['provider_rating'] = round(avg, 1)
        context['provider_review_count'] = user.average_rating[1]
        revenue = incoming.filter(status='completed').aggregate(total=Sum('service__price'))['total'] or 0
        context['revenue'] = revenue
        context['recent_incoming'] = incoming.select_related('client', 'service')[:5]
        context['recent_services'] = service_qs.select_related('category')[:5]

        # 7-day booking chart (dummy-friendly: real counts, zero-padded)
        labels, values = [], []
        for i in range(6, -1, -1):
            day = timezone.now().date() - timedelta(days=i)
            labels.append(day.strftime('%a'))
            values.append(incoming.filter(created_at__date=day).count())
        context['chart_labels'] = labels
        context['chart_values'] = values

        # Revenue by category (provider)
        cats = (
            service_qs.values('category__name')
            .annotate(total=Count('id'))
            .order_by('-total')[:6]
        )
        context['category_labels'] = [c['category__name'] or 'Uncategorized' for c in cats]
        context['category_values'] = [c['total'] for c in cats]

    # Client-specific
    if user.is_client:
        context['client_bookings'] = Booking.objects.filter(client=user).select_related('service', 'service__provider')[:5]
        context['reviews_given'] = Review.objects.filter(client=user).count()

        labels, values = [], []
        for i in range(6, -1, -1):
            day = timezone.now().date() - timedelta(days=i)
            labels.append(day.strftime('%a'))
            values.append(Booking.objects.filter(client=user, created_at__date=day).count())
        context['chart_labels'] = labels
        context['chart_values'] = values

    return render(request, 'dashboard/home.html', context)
