"""
URL configuration for ecoalerta project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('reportes.urls')),
]

