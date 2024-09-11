from django.urls import path
from . import views

app_name = 'yt'

urlpatterns = [
    path('home/', views.home, name='home'),
]