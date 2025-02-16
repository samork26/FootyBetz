from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Example view
    path('epl/', views.epl, name='learn_more'),
    path('contact/', views.contact, name='contact'),
]
