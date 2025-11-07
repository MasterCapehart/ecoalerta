"""
URL configuration for ecoalerta project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def root_view(request):
    """Vista raíz para evitar bucles de redirección"""
    return JsonResponse({
        'message': 'EcoAlerta API',
        'version': '1.0',
        'endpoints': {
            'api': '/api/',
            'admin': '/admin/'
        }
    })

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/', include('reportes.urls')),
]

