from django.urls import path
from . import views

app_name = 'file_converter'

urlpatterns = [
    path('upload/', views.upload_video, name='upload_video'),
    path('download/<str:file_path>/', views.download_file, name='download_file'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)