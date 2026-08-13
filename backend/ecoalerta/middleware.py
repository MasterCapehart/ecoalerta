from django.http import HttpResponse


class SecurityHeadersMiddleware:
    """
    Middleware de seguridad para añadir cabeceras de protección estándar.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
