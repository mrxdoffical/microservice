from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('fetch-formats/', views.home, name='fetch_formats'),
    path('download-video/', views.home, name='download_video'),
    path('search/', views.search_youtube, name='search_youtube'),
]