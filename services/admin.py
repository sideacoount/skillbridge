from django.contrib import admin

from .models import Category, Service, Wishlist


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'provider', 'category', 'price', 'availability',
                    'is_approved', 'created_at')
    list_filter = ('availability', 'is_approved', 'category', 'created_at')
    search_fields = ('title', 'description', 'provider__username')
    list_editable = ('is_approved', 'availability')
    date_hierarchy = 'created_at'
    actions = ['approve_services', 'hide_services']

    @admin.action(description='Approve selected services')
    def approve_services(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} service(s) approved.')

    @admin.action(description='Hide selected services')
    def hide_services(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} service(s) hidden.')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'created_at')
    search_fields = ('user__username', 'service__title')
