from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Example view
    path('about/', views.about, name='learn_more'),
    path('contact/', views.contact, name='contact'),
]
