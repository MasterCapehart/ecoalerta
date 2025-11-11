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
    """
    def process_response(self, request, response):
        # Si es una request a la API y hay una redirección, evitar que se procese
        if request.path.startswith('/api/') and response.status_code in [301, 302, 303, 307, 308]:
            # Para requests API, no deberíamos tener redirecciones
            # Si hay una redirección, algo está mal configurado
            # Devolver un error 500 en lugar de redirigir
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                from django.http import JsonResponse
                return JsonResponse({
                    'error': 'Redirección no esperada en endpoint API',
                    'path': request.path,
                    'method': request.method
                }, status=500)
        return response

