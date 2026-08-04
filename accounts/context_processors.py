from services.models import Category


def global_context(request):
    """Inject shared data (categories, unread counts) into every template."""
    ctx = {
        'all_categories': Category.objects.all().order_by('name'),
        'total_categories': Category.objects.count(),
    }
    if request.user.is_authenticated:
        ctx['unread_notification_count'] = request.user.unread_notifications()
    return ctx
