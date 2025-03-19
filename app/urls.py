from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('epl/', views.epl, name='epl'),
    path('match/<int:match_id>/', views.match_details, name='match_details'),
    path('api/matches/', views.get_matches, name='get_matches'),
]