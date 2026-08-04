from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.browse, name='browse'),
    path('services/search/', views.search_api, name='search_api'),
    path('services/providers/', views.providers, name='providers'),
    path('services/new/', views.create_service, name='create'),
    path('services/my/', views.my_services, name='my_services'),
    path('services/wishlist/', views.wishlist_view, name='wishlist'),
    path('services/<int:pk>/', views.detail, name='detail'),
    path('services/<int:pk>/edit/', views.update_service, name='update'),
    path('services/<int:pk>/delete/', views.delete_service, name='delete'),
    path('services/<int:pk>/wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
]
