from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.db.models import Count, Q
# NO usar GeoDjango - causa errores con GDAL en Azure
from django.db import connection

from .models import Reporte, CategoriaResiduo, Usuario
from .serializers import (
    ReporteSerializer, 
    ReporteDetalleSerializer,
    CategoriaResiduoSerializer,
    LoginSerializer,
    EstadisticasSerializer
)


class ReporteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar reportes de vertederos
    
    - GET /api/reportes/ : Listar reportes (público)
    - POST /api/reportes/ : Crear reporte (público)
    - GET /api/reportes/{id}/ : Ver detalle (público)
    - PATCH /api/reportes/{id}/actualizar_estado/ : Actualizar estado (requiere autenticación)
    - GET /api/reportes/estadisticas/ : Ver estadísticas (requiere autenticación)
    """
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer
    
    def get_permissions(self):
        """
        Permisos dinámicos:
        - Crear y listar reportes: público (AllowAny)
        - Actualizar estado y estadísticas: requiere autenticación
        """
        if self.action in ['create', 'list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ReporteDetalleSerializer
        return ReporteSerializer
    
    def get_queryset(self):
        queryset = Reporte.objects.select_related('categoria', 'asignado_a')
        
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
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Obtener lat y lng del request
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        
        if not lat or not lng:
            return Response(
                {'error': 'Debe proporcionar lat y lng'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear el objeto con la ubicación geográfica
        reporte = serializer.save()
        
        return Response({
            'codigo_seguimiento': reporte.codigo_seguimiento,
            'mensaje': 'Reporte creado exitosamente'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def actualizar_estado(self, request, pk=None):
        """
        Actualizar el estado de un reporte
        Requiere autenticación JWT
        """
        reporte = self.get_object()
        nuevo_estado = request.data.get('estado')
        notas = request.data.get('notas_internas', '')
        
        # Verificar que el usuario sea inspector o admin
        if request.user.tipo not in ['inspector', 'admin'] and not request.user.is_staff:
            return Response(
                {'error': 'No tienes permisos para actualizar reportes'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if nuevo_estado:
            reporte.estado = nuevo_estado
        if notas:
            reporte.notas_internas = notas
        
        # Asignar el usuario actual si no está asignado
        if not reporte.asignado_a:
            reporte.asignado_a = request.user
        
        reporte.save()
        
        serializer = self.get_serializer(reporte)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def estadisticas(self, request):
        """
        Obtener estadísticas de reportes
        Requiere autenticación JWT
        """
        # Verificar que el usuario sea inspector o admin
        if request.user.tipo not in ['inspector', 'admin'] and not request.user.is_staff:
            return Response(
                {'error': 'No tienes permisos para ver estadísticas'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
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
        
        return Response(data)


class CategoriaResiduoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para categorías de residuos (solo lectura)
    """
    queryset = CategoriaResiduo.objects.all()
    serializer_class = CategoriaResiduoSerializer
    permission_classes = [AllowAny]


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Endpoint para autenticación de usuarios
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
                return Response({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'tipo': user.tipo
                    }
                }, status=200)
            else:
                return Response(
                    {'error': 'No tienes permisos para acceder'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'Credenciales incorrectas'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def db_status_view(request):
    """
    Endpoint temporal para diagnosticar el estado de la base de datos
    """
    from django.db import connection
    
    status_info = {
        'database_connected': False,
        'table_exists': False,
        'columns_exist': False,
        'error': None
    }
    
    try:
        # Verificar conexión a la base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            status_info['database_connected'] = True
            
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'reportes_reporte'
                );
            """)
            table_exists = cursor.fetchone()[0]
            status_info['table_exists'] = table_exists
            
            if table_exists:
                # Verificar si las columnas existen
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'reportes_reporte'
                    AND column_name IN ('ubicacion_lat', 'ubicacion_lng');
                """)
                columns = [row[0] for row in cursor.fetchall()]
                status_info['columns_exist'] = len(columns) == 2
                status_info['found_columns'] = columns
                
    except Exception as e:
        status_info['error'] = str(e)
    
    return Response(status_info)


@api_view(['GET'])
@permission_classes([AllowAny])
def heatmap_view(request):
    """
    Endpoint para obtener datos de densidad de reportes para el mapa de calor.
    Versión simplificada sin PostGIS - agrupa reportes por cuadrícula aproximada.
    """
    try:
        # Parámetros opcionales con valores por defecto seguros
        try:
            radio = float(request.query_params.get('radio', 0.01))  # Radio en grados (~1km)
        except (ValueError, TypeError):
            radio = 0.01
        
        try:
            min_densidad = int(request.query_params.get('min_densidad', 1))
        except (ValueError, TypeError):
            min_densidad = 1
        
        # Aplicar filtros opcionales
        estado = request.query_params.get('estado')
        categoria_id = request.query_params.get('categoria')
        
        # Query simplificada sin PostGIS - agrupar por cuadrícula aproximada
        try:
            queryset = Reporte.objects.filter(
                ubicacion_lat__isnull=False,
                ubicacion_lng__isnull=False
            )
        except Exception as db_error:
            # Si hay un error de base de datos (columnas no existen), retornar vacío
            error_msg = str(db_error)
            if 'does not exist' in error_msg.lower() or 'column' in error_msg.lower():
                print(f"Error de base de datos: {error_msg}")
                return Response({
                    'data': [],
                    'total_points': 0,
                    'error': f'Error de base de datos. Las migraciones pueden no haberse aplicado correctamente. Error: {error_msg[:200]}',
                    'params': {}
                }, status=status.HTTP_200_OK)
            else:
                raise  # Re-lanzar si es otro tipo de error
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if categoria_id:
            try:
                categoria_id = int(categoria_id)
                queryset = queryset.filter(categoria_id=categoria_id)
            except (ValueError, TypeError):
                pass  # Ignorar si el ID no es válido
        
        # Agrupar manualmente por cuadrícula (aproximación)
        grid_size = radio * 2
        if grid_size <= 0:
            grid_size = 0.02  # Valor por defecto seguro
        
        heatmap_dict = {}
        
        for reporte in queryset:
            if reporte.ubicacion_lat is not None and reporte.ubicacion_lng is not None:
                try:
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
                except (TypeError, ValueError) as e:
                    continue  # Ignorar reportes con coordenadas inválidas
        
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
    except Exception as e:
        # Log del error para debugging
        import traceback
        print(f"Error en heatmap_view: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'data': [],
            'total_points': 0,
            'error': str(e),
            'params': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

