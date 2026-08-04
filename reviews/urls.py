from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('new/<int:provider_pk>/', views.create_review, name='create'),
    path('<int:pk>/edit/', views.edit_review, name='edit'),
    path('<int:pk>/delete/', views.delete_review, name='delete'),
]
