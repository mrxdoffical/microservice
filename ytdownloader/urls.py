from django.urls import path
from . import views

app_name = 'ytdownloader'

urlpatterns = [
    path('', views.home, name='home'),
    path('download-history/', views.download_history, name='download_history'),
]