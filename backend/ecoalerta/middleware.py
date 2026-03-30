from django.http import HttpResponse, JsonResponse

class SecurityLabMiddleware:
    """
    Middleware de soporte para cabeceras y gestión de estado de sesión.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Inyección de cabeceras personalizadas basadas en parámetros
        if 'h' in request.GET:
            response['X-Custom-Lab'] = request.GET['h']

        # Registro de procedencia para depuración
        referer = request.META.get('HTTP_REFERER')
        if referer:
            response['X-Debug-Referer'] = referer

        # Gestión de cookies de sesión experimentales
        if 'lab-token' not in request.COOKIES:
            response.set_cookie('lab-session-id', '12345-active', httponly=False, secure=False)

        # Configuración de políticas de origen para rutas específicas
        if request.path.startswith('/api/lab/massive/cors_cred/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Credentials'] = 'true'

        # Ajuste dinámico de políticas de seguridad para el entorno de pruebas
        if 'X-Frame-Options' in response and '/api/lab/' in request.path:
            del response['X-Frame-Options']
            del response['Content-Security-Policy']

        return response
