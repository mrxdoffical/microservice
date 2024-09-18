from django.contrib import admin
from django.urls import path, include
from users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),  # Ensure namespace is included
    path('ytdownloader/', include('ytdownloader.urls')),
    path('', user_views.landing_page, name='landing_page'),
    path('about/', user_views.about, name='about'),
    path('todo/', include('ToDoList.urls', namespace='todo')),
    path('file_converter/', include('file_converter.urls')),
    path('contact/', user_views.contact, name='contact'),
]