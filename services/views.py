from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from bookings.models import Booking
from reviews.models import Review

from .models import Service, Wishlist
from .forms import ServiceForm, ServiceFilterForm

SERVICE_CARD_PARTIAL = 'services/partials/service_cards.html'


def _visible_services():
    """Approved services only, in public views."""
    return Service.objects.filter(is_approved=True).select_related('provider', 'category')


def _apply_filters(request, queryset):
    """Apply the shared query/filter/sort logic (used by browse + search API)."""
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(provider__first_name__icontains=q)
            | Q(provider__last_name__icontains=q)
            | Q(provider__username__icontains=q)
            | Q(category__name__icontains=q)
        )

    category = request.GET.get('category')
    if category:
        queryset = queryset.filter(category__slug=category)

    min_price = _safe_decimal(request.GET.get('min_price'))
    max_price = _safe_decimal(request.GET.get('max_price'))
    if min_price is not None:
        queryset = queryset.filter(price__gte=min_price)
    if max_price is not None:
        queryset = queryset.filter(price__lte=max_price)

    availability = request.GET.get('availability')
    if availability:
        queryset = queryset.filter(availability=availability)

    min_rating = request.GET.get('min_rating')
    if min_rating:
        # Rating lives on the provider; annotate from reviews.
        queryset = queryset.annotate(
            _avg_rating=Avg('provider__reviews_received__rating'),
        ).filter(_avg_rating__gte=Decimal(min_rating))

    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        queryset = queryset.order_by('price')
    elif sort == 'price_high':
        queryset = queryset.order_by('-price')
    elif sort == 'rating':
        queryset = queryset.annotate(_r=Avg('provider__reviews_received__rating')).order_by('-created_at')
    elif sort == 'popular':
        queryset = queryset.annotate(_b=Count('bookings', distinct=True)).order_by('-created_at')
    else:
        queryset = queryset.order_by('-created_at')
    return queryset


def _safe_decimal(value):
    if not value:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        return None


def _card_grid(request, queryset):
    """Render the shared card-grid HTML (used by browse + AJAX live search)."""
    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = set(
            Wishlist.objects.filter(user=request.user).values_list('service_id', flat=True)
        )
    return render_to_string(
        SERVICE_CARD_PARTIAL,
        {'services': queryset, 'request': request, 'wishlist_ids': wishlist_ids},
        request=request,
    )


def home(request):
    """Landing page: hero, featured services, top providers, how it works, FAQ."""
    featured = _visible_services().annotate(
        _booking_count=Count('bookings', distinct=True)
    ).order_by('-_booking_count', '-created_at')[:6]

    top_providers = []
    from accounts.models import User
    providers = (
        User.objects.filter(role=User.Role.STUDENT, is_provider_approved=True)
        .prefetch_related('skills')
        .annotate(
            avg_rating=Avg('reviews_received__rating'),
            review_total=Count('reviews_received'),
            completed=Count('bookings_received', filter=Q(bookings_received__status='completed')),
        )
        .order_by('-completed', '-avg_rating')[:6]
    )
    for p in providers:
        if p.review_total:
            top_providers.append(p)

    stats = {
        'providers': User.objects.filter(role=User.Role.STUDENT, is_provider_approved=True).count(),
        'services': _visible_services().count(),
        'completed': Booking.objects.filter(status='completed').count(),
        'clients': User.objects.filter(role=User.Role.CLIENT).count(),
    }

    testimonials = [
        {'name': 'Sarah Mitchell', 'role': 'Startup founder', 'text':
         'SkillBridge connected us with a brilliant student developer who shipped our landing page in days. Quality work at a price our budget loved.', 'initials': 'SM'},
        {'name': 'David Chen', 'role': 'Photography student', 'text':
         'I turned my photography hobby into a steady income. Clients find me, book me, and pay me — all inside one clean app.', 'initials': 'DC'},
        {'name': 'Amara Okafor', 'role': 'E-commerce owner', 'text':
         'From logo design to product photography, every provider delivered on time. This platform feels far more polished than most marketplaces.', 'initials': 'AO'},
    ]

    faqs = [
        {'q': 'How does SkillBridge work?', 'a':
         'Students create a profile and list services. Clients browse, search and book directly. You negotiate through the app and pay outside it.'},
        {'q': 'Who can become a provider?', 'a':
         'Any verified student. After registering as a student, complete your profile and an admin approves your provider account.'},
        {'q': 'Is it really affordable?', 'a':
         'Yes. Because providers are students, prices are typically far below agency rates — without compromising quality.'},
        {'q': 'Can I cancel a booking?', 'a':
         'Clients can cancel pending bookings at any time from their dashboard. Completed work is final.'},
    ]

    context = {
        'featured': featured,
        'top_providers': top_providers,
        'testimonials': testimonials,
        'faqs': faqs,
        'stats': stats,
    }
    if request.user.is_authenticated:
        context['wishlist_ids'] = set(
            Wishlist.objects.filter(user=request.user).values_list('service_id', flat=True)
        )
    return render(request, 'landing/home.html', context)


def browse(request):
    """Browse all approved services with search, filters, sort and pagination."""
    queryset = _visible_services().select_related('provider', 'category')
    queryset = _apply_filters(request, queryset)

    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    filter_form = ServiceFilterForm(request.GET or None)
    active_filters = bool(
        request.GET.get('q') or request.GET.get('category')
        or request.GET.get('min_price') or request.GET.get('max_price')
        or request.GET.get('availability') or request.GET.get('min_rating')
    )

    qs_without_page = request.GET.copy()
    qs_without_page.pop('page', None)
    qs_without_page = qs_without_page.urlencode()

    context = {
        'page_obj': page_obj,
        'services': page_obj.object_list,
        'filter_form': filter_form,
        'query': request.GET.get('q', ''),
        'active_filters': active_filters,
        'qs_without_page': qs_without_page,
        'page_title': 'Browse services',
    }
    if request.user.is_authenticated:
        context['wishlist_ids'] = set(
            Wishlist.objects.filter(user=request.user).values_list('service_id', flat=True)
        )
    return render(request, 'services/browse.html', context)


def search_api(request):
    """AJAX endpoint returning rendered cards for live search/filtering."""
    queryset = _visible_services().select_related('provider', 'category')
    queryset = _apply_filters(request, queryset)
    count = queryset.count()
    html = _card_grid(request, queryset[:24])
    return JsonResponse({'html': html, 'count': count, 'query': request.GET.get('q', '')})


def detail(request, pk):
    service = get_object_or_404(_visible_services().select_related('provider'), pk=pk)
    reviews = Review.objects.filter(provider=service.provider).select_related('client')[:6]
    avg_rating, review_count = service.provider.average_rating
    similar = (
        _visible_services()
        .filter(category=service.category)
        .exclude(pk=service.pk)[:4]
    )
    if request.user.is_authenticated:
        from bookings.models import Booking
        in_wishlist = Wishlist.objects.filter(user=request.user, service=service).exists()
        existing_booking = Booking.objects.filter(service=service, client=request.user).first()
    else:
        in_wishlist = False
        existing_booking = None

    context = {
        'service': service,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': review_count,
        'similar': similar,
        'in_wishlist': in_wishlist,
        'existing_booking': existing_booking,
        'is_owner': request.user == service.provider,
        'wishlist_ids': {service.pk} if in_wishlist else set(),
    }
    return render(request, 'services/detail.html', context)


@login_required
def my_services(request):
    services = request.user.services.select_related('category')
    return render(request, 'services/my_services.html', {'services': services})


def _require_provider(user):
    """Guard used by provider-only views."""
    if user.is_anonymous or user.role != 'student' or not user.is_provider_approved:
        return True
    return False


@login_required
def create_service(request):
    if _require_provider(request.user):
        messages.error(
            request,
            'Only approved student providers can list services. '
            'Register as a student and wait for admin approval.',
        )
        return redirect('dashboard:home')

    form = ServiceForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        service = form.save(commit=False)
        service.provider = request.user
        service.save()
        messages.success(request, 'Your service has been published.')
        return redirect('services:my_services')
    return render(request, 'services/service_form.html', {'form': form, 'title': 'Create a service'})


@login_required
def update_service(request, pk):
    service = get_object_or_404(Service, pk=pk, provider=request.user)
    form = ServiceForm(request.POST or None, request.FILES or None, instance=service)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your service has been updated.')
        return redirect('services:my_services')
    return render(request, 'services/service_form.html', {'form': form, 'title': 'Edit service', 'service': service})


@login_required
@require_POST
def delete_service(request, pk):
    service = get_object_or_404(Service, pk=pk, provider=request.user)
    service.delete()
    messages.success(request, 'Service deleted.')
    return redirect('services:my_services')


@login_required
@require_POST
def toggle_wishlist(request, pk):
    service = get_object_or_404(Service, pk=pk)
    obj, created = Wishlist.objects.get_or_create(user=request.user, service=service)
    if not created:
        obj.delete()
        saved = False
        message = 'Removed from your wishlist.'
    else:
        saved = True
        message = 'Saved to your wishlist.'
    return JsonResponse({'saved': saved, 'message': message})


@login_required
def wishlist_view(request):
    items = request.user.wishlist.select_related('service', 'service__provider', 'service__category')
    wishlist_ids = {item.service_id for item in items}
    return render(request, 'services/wishlist.html', {
        'wishlist_items': items, 'wishlist_ids': wishlist_ids,
    })


def providers(request):
    """Directory of approved student providers."""
    from accounts.models import User
    providers = (
        User.objects.filter(role=User.Role.STUDENT, is_provider_approved=True)
        .prefetch_related('skills')
        .annotate(
            avg_rating=Avg('reviews_received__rating'),
            review_total=Count('reviews_received'),
            service_count=Count('services', filter=Q(services__is_approved=True)),
        )
        .order_by('-avg_rating', '-service_count')
    )
    q = request.GET.get('q', '').strip()
    if q:
        providers = providers.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q)
            | Q(username__icontains=q) | Q(skills__name__icontains=q)
        ).distinct()
    paginator = Paginator(providers, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'services/providers.html', {'page_obj': page_obj, 'providers': page_obj.object_list, 'query': q})
