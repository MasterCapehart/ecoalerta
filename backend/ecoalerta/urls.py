"""
URL configuration for ecoalerta project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework.permissions import AllowAny
from reportes.serializers import CustomTokenObtainPairSerializer
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

def root_view(request):
    """Vista raíz para evitar bucles de redirección"""
    # Devolver respuesta directa sin redirecciones
    response = JsonResponse({
        'message': 'EcoAlerta API',
        'version': '1.0',
        'status': 'ok',
        'endpoints': {
            'api': '/api/',
            'admin': '/admin/',
            'swagger': '/api/schema/swagger-ui/',
            'redoc': '/api/schema/redoc/',
            'schema': '/api/schema/',
            'jwt_login': '/api/auth/token/',
            'jwt_refresh': '/api/auth/token/refresh/',
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
    
    # JWT Authentication endpoints (públicos - no requieren autenticación)
    path('api/auth/token/', TokenObtainPairView.as_view(
        serializer_class=CustomTokenObtainPairSerializer,
        permission_classes=[AllowAny]
    ), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(
        permission_classes=[AllowAny]
    ), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(
        permission_classes=[AllowAny]
    ), name='token_verify'),
    
    # API Documentation (Swagger/OpenAPI) - públicos
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[AllowAny]), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(
        url_name='schema',
        permission_classes=[AllowAny]
    ), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(
        url_name='schema',
        permission_classes=[AllowAny]
    ), name='redoc'),
    
    # API endpoints
    path('api/', include('reportes.urls')),
]

