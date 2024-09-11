from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import about, landing_page

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='landing_page'), name='logout'),
    path('', views.home, name='home'),
    path('about/', about, name='about'),
    path('', landing_page, name='landing_page'),
]