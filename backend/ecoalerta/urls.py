"""
URL configuration for ecoalerta project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.conf.urls.static import static
import os

def root_view(request):
    """Vista raíz para evitar bucles de redirección"""
    # Devolver respuesta directa sin redirecciones
    response = JsonResponse({
        'message': 'UrbanAlert API',
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

def serve_media(request, path):
    """Vista personalizada para servir archivos media en producción"""
    import mimetypes
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        # Detectar el tipo MIME según la extensión
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        return FileResponse(open(file_path, 'rb'), content_type=content_type)
    return HttpResponse('File not found', status=404)

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/', include('reportes.urls')),
]

# Servir archivos media
if settings.DEBUG:
    # En desarrollo, usar el método estándar de Django
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # En producción, usar vista personalizada
    urlpatterns += [
        path('media/<path:path>', serve_media, name='media'),
    ]
