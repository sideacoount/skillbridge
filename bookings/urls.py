from django.urls import path

from . import views

app_name = 'bookings'

urlpatterns = [
    path('new/<int:service_pk>/', views.create_booking, name='create'),
    path('mine/', views.my_bookings, name='my_bookings'),
    path('incoming/', views.incoming_bookings, name='incoming'),
    path('<int:pk>/', views.booking_detail, name='detail'),
    path('<int:pk>/status/', views.update_status, name='update_status'),
    path('<int:pk>/cancel/', views.cancel_booking, name='cancel'),
    path('<int:pk>/delete/', views.delete_booking, name='delete'),
]
