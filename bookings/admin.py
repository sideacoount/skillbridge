from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('service', 'client', 'provider', 'status', 'preferred_date', 'budget', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('service__title', 'client__username', 'provider__username', 'description')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
