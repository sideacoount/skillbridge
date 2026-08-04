from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import User, Notification


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role',
                    'is_provider_approved', 'is_active', 'date_joined')
    list_filter = ('role', 'is_provider_approved', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    fieldsets = UserAdmin.fieldsets + (
        ('SkillBridge Profile', {
            'fields': ('role', 'phone', 'bio', 'occupation', 'location',
                       'website', 'profile_image', 'skills', 'is_provider_approved'),
        }),
    )
    actions = ['approve_providers', 'disapprove_providers']

    @admin.action(description='Approve selected providers')
    def approve_providers(self, request, queryset):
        updated = queryset.update(is_provider_approved=True)
        self.message_user(request, f'{updated} provider(s) approved.')

    @admin.action(description='Disapprove selected providers')
    def disapprove_providers(self, request, queryset):
        updated = queryset.update(is_provider_approved=False)
        self.message_user(request, f'{updated} provider(s) disapproved.')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')


admin.site.unregister(Group)
