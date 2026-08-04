from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('client', 'provider', 'service', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('client__username', 'provider__username', 'comment')
    list_editable = ('rating',)
    actions = ['delete_selected']
