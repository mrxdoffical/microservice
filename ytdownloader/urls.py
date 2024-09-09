from django.urls import path
from . import views

app_name = 'yt'

urlpatterns = [
    path('', views.home, name='home'),
]