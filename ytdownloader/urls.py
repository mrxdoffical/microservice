from django.urls import path
from . import views

app_name = 'yt'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('get_progress/', views.get_progress, name='get_progress'),
]