"""
URL configuration for ecoalerta project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.conf.urls.static import static

def root_view(request):
    """Vista raíz para evitar bucles de redirección"""
    # Devolver respuesta directa sin redirecciones
    response = JsonResponse({
        'message': 'EcoAlerta API',
        'version': '1.0',
        'status': 'ok',
        'endpoints': {
            'api': '/api/',
            'admin': '/admin/'
        }
    })
    # Asegurar que no haya redirecciones
    response.status_code = 200
    # Forzar headers para evitar cualquier redirección
    response['Location'] = None
    return response

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/', include('reportes.urls')),
]

# Servir archivos media (tanto en desarrollo como en producción para Azure)
# En Azure App Service, Django puede servir archivos media directamente
# NOTA: Para producción a gran escala, considera usar Azure Blob Storage
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
