"""
Middleware personalizado para manejar requests en Azure App Service
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse


class DisableCSRFForAPI(MiddlewareMixin):
    """
    Middleware para desactivar CSRF en endpoints API
    """
    def process_request(self, request):
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None


class PreventRedirectsMiddleware(MiddlewareMixin):
    """
    Middleware para prevenir redirecciones no deseadas en API endpoints
    Se ejecuta PRIMERO para interceptar redirecciones antes de que se generen
    """
    def process_response(self, request, response):
        # Si es una request a la API y hay una redirección, interceptarla
        if request.path.startswith('/api/') and response.status_code in [301, 302, 303, 307, 308]:
            # Obtener la URL de redirección
            location = response.get('Location', '')
            request_url = request.build_absolute_uri()
            
            # Verificar si la redirección es a la misma URL o muy similar (bucle)
            if location:
                # Normalizar URLs para comparación
                location_normalized = location.rstrip('/')
                request_url_normalized = request_url.rstrip('/')
                
                # Si la redirección es a la misma URL, evitar el bucle
                if location_normalized == request_url_normalized or location_normalized in request_url_normalized:
                    from django.http import JsonResponse
                    # Para requests POST/PUT/PATCH/DELETE, devolver error
                    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                        return JsonResponse({
                            'error': 'Bucle de redirección detectado',
                            'path': request.path,
                            'method': request.method,
                            'message': 'El servidor está redirigiendo a la misma URL. Esto indica un problema de configuración.'
                        }, status=500)
                    # Para GET, intentar seguir la redirección pero sin crear bucle
                    # En este caso, simplemente devolvemos un error también
                    return JsonResponse({
                        'error': 'Redirección detectada',
                        'path': request.path,
                        'location': location
                    }, status=500)
            
            # Para cualquier otra redirección en API, devolver error
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Redirección no esperada en endpoint API',
                    'path': request.path,
                    'method': request.method,
                    'location': location
                }, status=500)
        return response

