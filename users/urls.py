# users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('main/', views.main_page, name='main_page'),
    path('contact/', views.contact, name='contact'),
    path('logout/', views.user_logout, name='logout'),
    path('', views.landing_page, name='landing_page'),  # Ensure this URL pattern is defined
]