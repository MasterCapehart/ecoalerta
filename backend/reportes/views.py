from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import os
import logging

from django.conf import settings
from django.db.models import Count, Q
from django.core.cache import cache

from .models import Reporte, CategoriaResiduo, Usuario
from .serializers import (
    ReporteSerializer, 
    ReporteDetalleSerializer,
    CategoriaResiduoSerializer,
    LoginSerializer,
    EstadisticasSerializer,
    ReportePredictionRequestSerializer,
    ReportePredictionResponseSerializer,
)
from .ml import ReportResolutionPredictor
from .ml.exceptions import PredictionModelNotFound, PredictionModelNotReady
from .permissions import IsInspectorOrReadOnly, IsInspector, AllowPublicCreate
from .services import ReporteService

logger = logging.getLogger('reportes')

LOCAL_PREDICTIONS_ENABLED = (
    settings.DEBUG
    or os.getenv("ENABLE_LOCAL_PREDICTIONS", "false").lower() in ("1", "true", "yes")
)


class ReporteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar reportes de vertederos
    """
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer
    permission_classes = [AllowPublicCreate]  # Permite crear sin auth, pero requiere auth para otras operaciones
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReporteDetalleSerializer
        return ReporteSerializer
    
    def get_serializer_context(self):
        """Asegurar que el request siempre esté en el contexto del serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        # Optimizar consultas con select_related y prefetch_related
        queryset = Reporte.objects.select_related(
            'categoria', 
            'asignado_a', 
            'creado_por'
        ).prefetch_related('notificaciones')
        
        # Filtros
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        categoria_id = self.request.query_params.get('categoria')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        
        codigo = self.request.query_params.get('codigo')
        if codigo:
            queryset = queryset.filter(codigo_seguimiento__icontains=codigo)
        
        return queryset.order_by('-fecha_creacion')
    
    def create(self, request, *args, **kwargs):
        # Log estructurado
        logger.info(f"Creando reporte - Foto recibida: {request.FILES.get('foto')}")
        if request.FILES.get('foto'):
            logger.debug(f"Nombre del archivo: {request.FILES['foto'].name}")
            logger.debug(f"Tamaño: {request.FILES['foto'].size} bytes")
        
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Obtener lat y lng del request
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if not lat or not lng:
            logger.warning("Intento de crear reporte sin coordenadas")
            return Response(
                {'error': 'Debe proporcionar lat y lng'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Asignar usuario si está autenticado
        if request.user.is_authenticated:
            serializer.save(creado_por=request.user)
        else:
            serializer.save()
        
        reporte = serializer.instance
        
        # Log después de guardar
        if reporte.foto:
            logger.info(f"Foto guardada: {reporte.foto.name}")
            try:
                logger.debug(f"Ruta completa: {reporte.foto.path}")
            except Exception as e:
                logger.error(f"No se pudo obtener ruta: {e}")
        else:
            logger.warning("No se guardó la foto")
        
        logger.info(f"Reporte creado exitosamente: {reporte.codigo_seguimiento}")
        
        return Response({
            'codigo_seguimiento': reporte.codigo_seguimiento,
            'mensaje': 'Reporte creado exitosamente'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsInspector])
    def actualizar_estado(self, request, pk=None):
        """Actualizar el estado de un reporte (solo inspectores)"""
        reporte = self.get_object()
        nuevo_estado = request.data.get('estado')
        notas = request.data.get('notas_internas', '')
        
        if nuevo_estado:
            reporte.estado = nuevo_estado
        if notas:
            reporte.notas_internas = notas
        
        reporte.save()
        
        logger.info(f"Estado actualizado para reporte {reporte.codigo_seguimiento} por {request.user.username}")
        
        serializer = self.get_serializer(reporte)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsInspector])
    def estadisticas(self, request):
        """Obtener estadísticas de reportes (solo inspectores)"""
        # Intentar obtener de caché
        cache_key = 'reportes_estadisticas'
        data = cache.get(cache_key)
        
        if data is None:
            total = Reporte.objects.count()
            nuevos = Reporte.objects.filter(estado='nuevo').count()
            en_proceso = Reporte.objects.filter(estado='proceso').count()
            resueltos = Reporte.objects.filter(estado='resuelto').count()
            
            data = {
                'total': total,
                'nuevos': nuevos,
                'en_proceso': en_proceso,
                'resueltos': resueltos
            }
            
            # Guardar en caché por 5 minutos
            cache.set(cache_key, data, 300)
        
        return Response(data)
    
    @action(detail=False, methods=['get'], url_path='exportar', permission_classes=[IsInspector])
    def exportar_csv(self, request):
        """
        Exporta reportes a CSV (solo inspectores)
        """
        from django.http import HttpResponse
        
        # Aplicar los mismos filtros que get_queryset
        queryset = self.get_queryset()
        
        # Generar CSV
        csv_content = ReporteService.exportar_a_csv(queryset)
        
        # Crear respuesta HTTP
        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="reportes.csv"'
        
        logger.info(f"Exportación CSV realizada por {request.user.username}")
        return response
    
    @action(detail=False, methods=['post'], url_path='predicciones')
    def predicciones(self, request):
        """Generar predicciones de resolución usando el modelo local."""
        if not LOCAL_PREDICTIONS_ENABLED:
            return Response(
                {
                    'detail': 'Las predicciones solo están disponibles en entornos locales.',
                    'enabled': False,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        serializer = ReportePredictionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.to_feature_payload()
        
        try:
            predictor = ReportResolutionPredictor.load()
            result = predictor.predict_from_payload(payload)
        except PredictionModelNotFound:
            try:
                predictor = ReportResolutionPredictor.train_from_queryset()
                result = predictor.predict_from_payload(payload)
            except PredictionModelNotReady:
                result = ReportResolutionPredictor.fallback_prediction(payload)
        except PredictionModelNotReady:
            result = ReportResolutionPredictor.fallback_prediction(payload)
        
        response_serializer = ReportePredictionResponseSerializer(result.as_dict())
        return Response(response_serializer.data)


class CategoriaResiduoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para categorías de residuos (solo lectura)
    """
    queryset = CategoriaResiduo.objects.all()
    serializer_class = CategoriaResiduoSerializer
    permission_classes = [AllowAny]  # Categorías son públicas
    
    def get_queryset(self):
        # Intentar obtener de caché
        cache_key = 'categorias_list'
        categorias = cache.get(cache_key)
        
        if categorias is None:
            categorias = list(CategoriaResiduo.objects.all())
            # Guardar en caché por 1 hora (categorías cambian poco)
            cache.set(cache_key, categorias, 3600)
        
        return categorias


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Endpoint para autenticación de usuarios con JWT
    Maneja tanto POST como GET para evitar redirecciones
    """
    # Si es GET, devolver información del endpoint sin redirección
    if request.method == 'GET':
        return Response({
            'endpoint': '/api/auth/login/',
            'method': 'POST',
            'message': 'Este endpoint requiere POST con username y password'
        }, status=200)
    
    # Procesar POST normalmente
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user:
            # Verificar si es inspector
            if user.tipo == 'inspector' or user.is_staff:
                # Generar tokens JWT
                refresh = RefreshToken.for_user(user)
                
                logger.info(f"Login exitoso para usuario: {username}")
                
                return Response({
                    'success': True,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'tipo': user.tipo
                    }
                }, status=200)
            else:
                logger.warning(f"Intento de login sin permisos: {username}")
                return Response(
                    {'error': 'No tienes permisos para acceder'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            logger.warning(f"Intento de login con credenciales incorrectas: {username}")
            return Response(
                {'error': 'Credenciales incorrectas'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint de health check para monitoreo
    """
    from django.db import connection
    
    try:
        # Verificar conexión a la base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return Response({
            'status': 'healthy',
            'database': 'connected',
            'version': '1.0.0'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Health check falló: {e}")
        return Response({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    Endpoint para refrescar tokens JWT
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    from rest_framework_simplejwt.exceptions import TokenError
    
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {'error': 'Token de refresh requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = refresh.access_token
        
        return Response({
            'access': str(access_token),
        }, status=status.HTTP_200_OK)
    except TokenError as e:
        logger.warning(f"Error al refrescar token: {e}")
        return Response(
            {'error': 'Token inválido o expirado'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def heatmap_view(request):
    """
    Endpoint para obtener datos de densidad de reportes para el mapa de calor.
    Versión simplificada sin PostGIS - agrupa reportes por cuadrícula aproximada.
    """
    # Parámetros opcionales
    radio = float(request.query_params.get('radio', 0.01))  # Radio en grados (~1km)
    min_densidad = int(request.query_params.get('min_densidad', 1))
    
    # Aplicar filtros opcionales
    estado = request.query_params.get('estado')
    categoria_id = request.query_params.get('categoria')
    
    # Query simplificada sin PostGIS - agrupar por cuadrícula aproximada
    queryset = Reporte.objects.filter(
        ubicacion_lat__isnull=False,
        ubicacion_lng__isnull=False
    )
    
    if estado:
        queryset = queryset.filter(estado=estado)
    if categoria_id:
        queryset = queryset.filter(categoria_id=categoria_id)
    
    # Agrupar manualmente por cuadrícula (aproximación)
    grid_size = radio * 2
    heatmap_dict = {}
    
    for reporte in queryset:
        if reporte.ubicacion_lat and reporte.ubicacion_lng:
            # Redondear a la cuadrícula
            grid_lat = round(reporte.ubicacion_lat / grid_size) * grid_size
            grid_lng = round(reporte.ubicacion_lng / grid_size) * grid_size
            key = (grid_lat, grid_lng)
            
            if key not in heatmap_dict:
                heatmap_dict[key] = {
                    'lat': grid_lat,
                    'lng': grid_lng,
                    'densidad': 0
                }
            heatmap_dict[key]['densidad'] += 1
    
    # Filtrar por densidad mínima y formatear
    heatmap_data = [
        {
            'lat': item['lat'],
            'lng': item['lng'],
            'intensity': item['densidad'],
            'densidad': item['densidad']
        }
        for item in heatmap_dict.values()
        if item['densidad'] >= min_densidad
    ]
    
    # Ordenar por densidad
    heatmap_data.sort(key=lambda x: x['densidad'], reverse=True)
    
    return Response({
        'data': heatmap_data,
        'total_points': len(heatmap_data),
        'params': {
            'radio': radio,
            'min_densidad': min_densidad
        }
    })
