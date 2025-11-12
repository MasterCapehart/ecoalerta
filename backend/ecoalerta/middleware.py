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
    Se ejecuta ÚLTIMO para interceptar redirecciones después de todos los otros middlewares
    """
    def process_response(self, request, response):
        # Interceptar TODAS las redirecciones en API endpoints - FORZAR interceptación
        if request.path.startswith('/api/'):
            # Si hay cualquier redirección (incluso si es a la misma URL)
            if response.status_code in [301, 302, 303, 307, 308]:
                location = response.get('Location', '')
                request_url = request.build_absolute_uri()
                
                # NUNCA permitir redirecciones en API - devolver error inmediatamente
                logger.error(f"🚨 REDIRECCIÓN BLOQUEADA EN API: {request.path} -> {location}")
                logger.error(f"   Request URL: {request_url}")
                logger.error(f"   Method: {request.method}")
                logger.error(f"   Status: {response.status_code}")
                
                # Devolver respuesta JSON directamente sin redirección
                return JsonResponse({
                    'error': 'Redirección bloqueada en endpoint API',
                    'path': request.path,
                    'method': request.method,
                    'status_code': response.status_code,
                    'location': location,
                    'request_url': request_url,
                    'message': 'Las redirecciones no están permitidas en endpoints API.',
                    'fix': 'Verifica la configuración de Django y Azure. SecurityMiddleware y CommonMiddleware deben estar desactivados.'
                }, status=400)
            
            # Si no hay redirección pero la respuesta no es exitosa, loggear para debugging
            if response.status_code >= 400:
                logger.warning(f"⚠️ Respuesta de error en API: {request.path} -> {response.status_code}")
        
        # Interceptar redirecciones en la raíz
        if request.path == '/' and response.status_code in [301, 302, 303, 307, 308]:
            location = response.get('Location', '')
            logger.error(f"🚨 Redirección bloqueada en raíz: {location}")
            # Devolver respuesta JSON en lugar de redirección
            return JsonResponse({
                'error': 'Redirección bloqueada en raíz',
                'path': request.path,
                'location': location,
                'message': 'Las redirecciones en la raíz no están permitidas.'
            }, status=400)
        
        return response

