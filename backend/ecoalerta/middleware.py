"""
Middleware personalizado para manejar requests en Azure App Service
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse, JsonResponse
import logging

logger = logging.getLogger(__name__)


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
    Se ejecuta DESPUÉS de SecurityMiddleware para interceptar sus redirecciones
    """
    def process_response(self, request, response):
        # Interceptar TODAS las redirecciones en API endpoints
        if request.path.startswith('/api/') and response.status_code in [301, 302, 303, 307, 308]:
            location = response.get('Location', '')
            request_url = request.build_absolute_uri()
            
            # Log para debugging
            logger.warning(f"Redirección detectada en API: {request.path} -> {location}")
            
            # Para TODAS las redirecciones en API, devolver error JSON
            # Esto evita bucles y proporciona información de debugging
            return JsonResponse({
                'error': 'Redirección detectada en endpoint API',
                'path': request.path,
                'method': request.method,
                'status_code': response.status_code,
                'location': location,
                'request_url': request_url,
                'message': 'Las redirecciones no están permitidas en endpoints API. Esto indica un problema de configuración.'
            }, status=500)
        
        # También interceptar redirecciones en la raíz si es necesario
        if request.path == '/' and response.status_code in [301, 302, 303, 307, 308]:
            location = response.get('Location', '')
            # Si la redirección es a la misma URL, evitar el bucle
            if location and location.rstrip('/') == request.build_absolute_uri('/').rstrip('/'):
                logger.warning(f"Bucle de redirección detectado en raíz: {location}")
                return JsonResponse({
                    'error': 'Bucle de redirección detectado',
                    'path': request.path,
                    'location': location,
                    'message': 'El servidor está redirigiendo a la misma URL.'
                }, status=500)
        
        return response

