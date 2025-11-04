from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.db.models import Count, Q

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
    """
    queryset = Reporte.objects.all()
    serializer_class = ReporteSerializer
    permission_classes = [AllowAny]
    
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
    
    @action(detail=True, methods=['patch'])
    def actualizar_estado(self, request, pk=None):
        """Actualizar el estado de un reporte"""
        reporte = self.get_object()
        nuevo_estado = request.data.get('estado')
        notas = request.data.get('notas_internas', '')
        
        if nuevo_estado:
            reporte.estado = nuevo_estado
        if notas:
            reporte.notas_internas = notas
        
        reporte.save()
        
        serializer = self.get_serializer(reporte)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtener estadísticas de reportes"""
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


@api_view(['POST'])
def login_view(request):
    """
    Endpoint para autenticación de usuarios
    """
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
                })
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

