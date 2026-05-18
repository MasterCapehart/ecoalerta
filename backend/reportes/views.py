from django.shortcuts import get_object_or_404, redirect
from django.db import connection, transaction
from django.http import JsonResponse, HttpResponse
from django.template import Template, Context
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import os
import logging
import hashlib
import traceback
import requests
import pickle
import base64
import jwt
import random
import re
import time
import xml.etree.ElementTree as ET
from PIL import Image, ExifTags

from django.conf import settings
from django.db.models import Count, Q, Avg
from django.core.cache import cache

from .models import (
    Reporte,
    CategoriaResiduo,
    Usuario,
    Tag,
    HistorialCambio,
    ComentarioPublico,
    BusquedaGuardada,
    CierreReporte,
    ReporteImagen,
    Notificacion,
)
from .serializers import (
    ReporteSerializer, 
    ReporteDetalleSerializer,
    CategoriaResiduoSerializer,
    LoginSerializer,
    EstadisticasSerializer,
    ReportePredictionRequestSerializer,
    ReportePredictionResponseSerializer,
    UsuarioSerializer,
    ActualizarUbicacionSerializer,
    BusquedaGuardadaSerializer,
    NotificacionSerializer,
    PublicReporteSerializer,
)
from .throttling import ReportSubmissionAnonThrottle, ReportSubmissionProRateThrottle
from .ml import ReportResolutionPredictor
from .ml.exceptions import PredictionModelNotFound, PredictionModelNotReady
from .permissions import IsInspectorOrReadOnly, IsInspector, AllowPublicCreate
from .services import ReporteService
from .search_service import SearchService
from .priority_service import PriorityService
from .assignment_service import AssignmentService
from .routing_service import RoutingService
from .validation_service import ValidationService
from .geocoding_service import GeocodingService
from .notification_service import NotificationService
from .history_service import HistoryService
from .reports_service import ReportsService
from .duplicate_service import DuplicateDetectionService
from .sla_service import SLAService
from .intelligence_service import IntelligenceService
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('reportes')

LOCAL_PREDICTIONS_ENABLED = (
    settings.DEBUG
    or os.getenv("ENABLE_LOCAL_PREDICTIONS", "false").lower() in ("1", "true", "yes")
)


class ReporteViewSet(viewsets.ModelViewSet):
   
    queryset = Reporte.objects.all().order_by('-fecha_creacion')
    serializer_class = ReporteSerializer
    
    throttle_classes = [ReportSubmissionAnonThrottle, ReportSubmissionProRateThrottle]
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            permission_classes = [AllowPublicCreate]
        elif self.action in ['update', 'partial_update', 'destroy', 'actualizar_estado', 'bulk_update']:
            permission_classes = [IsAuthenticated, IsInspectorOrReadOnly]
        else:
            permission_classes = [AllowAny] # For list and retrieve
        return [permission() for permission in permission_classes]
    
    def get_throttles(self):
        """Aplicar throttling estricto solo para crear reportes, relajado para el resto"""
        if self.action == 'create':
            return [ReportSubmissionAnonThrottle(), ReportSubmissionProRateThrottle()]
        # Para lectura y otras acciones, usar throttling estándar
        return [UserRateThrottle(), AnonRateThrottle()]
    
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
        ).prefetch_related('notificaciones', 'tags', 'historial')
        
        # Usar servicio de búsqueda avanzada si hay parámetros de búsqueda
        search_params = {}
        for key in ['q', 'estado', 'categoria', 'asignado_a', 'prioridad', 'tags', 
                    'fecha_desde', 'fecha_hasta', 'lat', 'lng', 'radio', 'es_spam', 
                    'validado', 'ordenar_por', 'orden']:
            value = self.request.query_params.get(key)
            if value is not None:
                if key in ['categoria', 'asignado_a']:
                    try:
                        search_params[key] = int(value)
                    except ValueError:
                        pass
                elif key in ['lat', 'lng', 'radio']:
                    try:
                        search_params[key] = float(value)
                    except ValueError:
                        pass
                elif key == 'tags':
                    # Tags puede ser lista separada por comas
                    search_params[key] = [int(t) for t in value.split(',') if t.isdigit()]
                elif key == 'es_spam' or key == 'validado':
                    search_params[key] = value.lower() in ('true', '1', 'yes')
                else:
                    search_params[key] = value
        
        # Si hay parámetros de búsqueda, usar SearchService
        if search_params:
            queryset = SearchService.search_reportes(queryset, search_params)
        else:
            # Filtros básicos para compatibilidad
            estado = self.request.query_params.get('estado')
            if estado:
                queryset = queryset.filter(estado=estado)
            
            categoria_id = self.request.query_params.get('categoria')
            if categoria_id:
                queryset = queryset.filter(categoria_id=categoria_id)
            
            codigo = self.request.query_params.get('codigo')
            if codigo:
                queryset = queryset.filter(codigo_seguimiento__icontains=codigo)
            
            # Ordenamiento por defecto
            ordenar_por = self.request.query_params.get('ordenar_por', 'fecha_creacion')
            orden = self.request.query_params.get('orden', 'desc')
            if orden == 'desc':
                ordenar_por = f'-{ordenar_por}'
            queryset = queryset.order_by(ordenar_por)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def clusters(self, request):
        """
        Retorna clusters de reportes basados en grid.
        Params: 
        - zoom: Nivel de zoom (determina el tamaño del grid)
        - bbox: min_lng,min_lat,max_lng,max_lat (opcional)
        """
        try:
            from django.contrib.gis.db.models.functions import SnapToGrid
            from django.db.models import Count
            
            zoom = int(request.query_params.get('zoom', 12))
            
            # Tamaño del grid basado en zoom (aproximación simple)
            # Zoom 12 ~ 0.01 grados, Zoom 18 ~ 0.0001
            grid_size = 0.05 / (2 ** (zoom - 10)) if zoom > 10 else 0.05
            
            queryset = self.get_queryset()
            
            # Agrupar por grid
            clusters = queryset.annotate(
                location_cluster=SnapToGrid('ubicacion', grid_size)
            ).values('location_cluster').annotate(
                count=Count('id'),
                # Podríamos agregar más agregaciones aquí (e.j. prioridad promedio)
            ).order_by()
            
            data = []
            for cluster in clusters:
                if cluster['location_cluster']:
                    data.append({
                        'lat': cluster['location_cluster'].y,
                        'lng': cluster['location_cluster'].x,
                        'count': cluster['count']
                    })
                    
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def verificar_duplicados(self, request):
        """
        Endpoint para verificar reportes duplicados cercanos.
        Params: lat, lng, radio (opcional, por defecto 50m)
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radio = request.query_params.get('radio', 50)
        descripcion = request.query_params.get('descripcion', '')
        categoria_id = request.query_params.get('categoria')
        
        if not lat or not lng:
            return Response(
                {"error": "Se requieren parámetros 'lat' y 'lng'."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            radio = int(radio)
            if radio < 5:
                radio = 5
            if radio > 500:
                radio = 500

            categoria_id_int = int(categoria_id) if categoria_id and str(categoria_id).isdigit() else None
            duplicates_qs = DuplicateDetectionService.check_potential_duplicates(
                lat=lat,
                lng=lng,
                radius_meters=radio,
            )
            duplicates_count = duplicates_qs.count()
            duplicates_ranked = DuplicateDetectionService.find_ranked_duplicates(
                lat=lat,
                lng=lng,
                descripcion=descripcion,
                categoria_id=categoria_id_int,
                radius_meters=radio,
                limit=5,
            )
            serializer = self.get_serializer([item['reporte'] for item in duplicates_ranked], many=True)
            ranked_payload = []
            for data, ranked in zip(serializer.data, duplicates_ranked):
                ranked_payload.append({
                    **data,
                    'duplicate_score': ranked['score'],
                    'duplicate_level': ranked['nivel'],
                    'distance_meters': ranked['distance_meters'],
                })
            return Response({
                "found": duplicates_count > 0,
                "count": duplicates_count,
                "radius_meters": radio,
                "duplicates": ranked_payload
            })
        except Exception as e:
             return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def public_map(self, request):
        """Endpoint público ligero para el mapa colaborativo"""
        # Filtros
        categoria_id = request.query_params.get('categoria')
        dias = request.query_params.get('dias')
        
        # Solo reportes activos (no resueltos ni spam)
        queryset = Reporte.objects.filter(
            es_spam=False
        ).exclude(estado='resuelto')
        
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
            
        if dias:
            from datetime import timedelta
            from django.utils import timezone
            try:
                days_ago = int(dias)
                since_date = timezone.now() - timedelta(days=days_ago)
                queryset = queryset.filter(fecha_creacion__gte=since_date)
            except ValueError:
                pass

        queryset = queryset.order_by('-fecha_creacion')[:200] # Limite para performance
        
        serializer = PublicReporteSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def validate_report(self, request, pk=None):
        """Acción ciudadana: 'Lo veo también'"""
        reporte = self.get_object()
        reporte.validaciones_ciudadanas += 1
        reporte.save()
        return Response({'status': 'validated', 'new_count': reporte.validaciones_ciudadanas})

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
        
        # Validar ubicación
        es_valido, mensaje = ValidationService.validate_location(float(lat), float(lng))
        if not es_valido:
            return Response(
                {'error': f'Ubicación inválida: {mensaje}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Asignar usuario si está autenticado
        if request.user.is_authenticated:
            serializer.save(creado_por=request.user)
        else:
            serializer.save()
        
        reporte = serializer.instance
        
        # Procesar tags si se proporcionaron
        tags_ids = request.data.get('tags', [])
        if tags_ids:
            if isinstance(tags_ids, str):
                tags_ids = [int(t) for t in tags_ids.split(',') if t.isdigit()]
            reporte.tags.set(tags_ids)
        
        # Validar y detectar spam
        validation_result = ValidationService.validate_and_score(reporte)
        reporte.save(update_fields=['es_spam', 'score_confianza'])
        
        # Si no se proporcionó dirección, intentar geocodificación inversa (asíncrona)
        direccion_proporcionada = request.data.get('direccion', '').strip()
        if direccion_proporcionada:
            # Si viene del frontend, usar esa dirección
            reporte.direccion = direccion_proporcionada
            reporte.direccion_completa = direccion_proporcionada
            reporte.save(update_fields=['direccion', 'direccion_completa'])
        else:
            # Geocodificación asíncrona
            from .tasks import geocodificar_reporte_async
            geocodificar_reporte_async.delay(reporte.id)
        
        # Calcular prioridad
        reporte.prioridad_calculada = PriorityService.calculate_priority_score(reporte)
        reporte.save(update_fields=['prioridad_calculada'])
        
        # Calcular SLA automáticamente (asíncrono)
        from .tasks import calcular_sla_automatico
        calcular_sla_automatico.delay(reporte.id)
        
        # Registrar en historial
        HistoryService.record_change(
            reporte,
            'estado',
            None,
            reporte.estado,
            request.user if request.user.is_authenticated else None,
            'Reporte creado'
        )
        
        # Notificar a inspectores (asíncrono)
        try:
            from .tasks import enviar_email_notificacion_async
            from .models import Usuario
            inspectores = Usuario.objects.filter(tipo='inspector', is_active=True)
            for inspector in inspectores:
                if inspector.email:
                    asunto = f"Nuevo reporte: {reporte.codigo_seguimiento}"
                    mensaje = f"""
                    <h2>Nuevo Reporte Creado</h2>
                    <p><strong>Código:</strong> {reporte.codigo_seguimiento}</p>
                    <p><strong>Categoría:</strong> {reporte.categoria.nombre if reporte.categoria else 'N/A'}</p>
                    <p><strong>Ubicación:</strong> {reporte.direccion or 'N/A'}</p>
                    <p><strong>Descripción:</strong> {reporte.descripcion[:100]}...</p>
                    """
                    enviar_email_notificacion_async.delay(inspector.email, asunto, mensaje)
        except Exception as e:
            logger.warning(f"No se pudo enviar notificación: {e}")
        
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
        cache.delete('reportes_estadisticas')
        
        return Response({
            'codigo_seguimiento': reporte.codigo_seguimiento,
            'mensaje': 'Reporte creado exitosamente',
            'score_confianza': reporte.score_confianza,
            'es_spam': reporte.es_spam
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsInspector])
    def actualizar_estado(self, request, pk=None):
        """Actualizar el estado de un reporte (solo inspectores)"""
        reporte = self.get_object()
        estado_anterior = reporte.estado
        nuevo_estado = request.data.get('estado')
        notas = request.data.get('notas_internas', '')
        asignado_a_id = request.data.get('asignado_a')
        prioridad = request.data.get('prioridad')
        tags_ids = request.data.get('tags')
        evidencia_cierre = (request.data.get('evidencia_cierre') or '').strip()
        foto_cierre = request.FILES.get('foto_cierre')
        cierre_existente = getattr(reporte, 'cierre', None)
        
        cambios = []

        if nuevo_estado in ['resuelto', 'cerrado']:
            evidencia_valida = bool(evidencia_cierre) or bool(foto_cierre) or bool(
                cierre_existente and (
                    (cierre_existente.evidencia_texto and cierre_existente.evidencia_texto.strip())
                    or cierre_existente.foto_cierre
                )
            )
            if not evidencia_valida:
                return Response(
                    {'error': 'Para resolver/cerrar un reporte debes adjuntar evidencia (texto o fotografía de cierre).'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if nuevo_estado and nuevo_estado != estado_anterior:
            reporte.estado = nuevo_estado
            cambios.append('estado')
            
            # Calcular tiempo de resolución si se resuelve
            if nuevo_estado == 'resuelto' and reporte.fecha_creacion:
                tiempo = (timezone.now() - reporte.fecha_creacion).total_seconds() / 3600
                reporte.tiempo_resolucion_horas = tiempo
                
                # Notificar resolución
                try:
                    NotificationService.notify_resolution(reporte)
                except Exception as e:
                    logger.warning(f"No se pudo enviar notificación de resolución: {e}")

        if nuevo_estado in ['resuelto', 'cerrado'] and (evidencia_cierre or foto_cierre):
            cierre, _ = CierreReporte.objects.get_or_create(
                reporte=reporte,
                defaults={
                    'cerrado_por': request.user,
                    'evidencia_texto': evidencia_cierre,
                }
            )
            if evidencia_cierre:
                cierre.evidencia_texto = evidencia_cierre
            if foto_cierre:
                cierre.foto_cierre = foto_cierre
                ReporteImagen.objects.create(reporte=reporte, imagen=foto_cierre)
            cierre.cerrado_por = request.user
            cierre.save()
        
        if notas:
            notas_anterior = reporte.notas_internas
            reporte.notas_internas = notas
            if notas_anterior != notas:
                cambios.append('notas')
        
        if asignado_a_id:
            inspector_anterior = reporte.asignado_a
            try:
                nuevo_inspector = Usuario.objects.get(id=asignado_a_id, tipo='inspector')
                reporte.asignado_a = nuevo_inspector
                cambios.append('asignacion')
                
                # Notificar asignación
                try:
                    NotificationService.notify_assignment(reporte, nuevo_inspector)
                except Exception as e:
                    logger.warning(f"No se pudo enviar notificación de asignación: {e}")
            except Usuario.DoesNotExist:
                return Response(
                    {'error': 'Inspector no encontrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if prioridad:
            prioridad_anterior = reporte.prioridad
            reporte.prioridad = prioridad
            if prioridad_anterior != prioridad:
                cambios.append('prioridad')
            # Recalcular prioridad calculada
            reporte.prioridad_calculada = PriorityService.calculate_priority_score(reporte)
        
        if tags_ids is not None:
            tags_anterior = list(reporte.tags.all())
            if isinstance(tags_ids, str):
                tags_ids = [int(t) for t in tags_ids.split(',') if t.isdigit()]
            reporte.tags.set(tags_ids)
            tags_nuevo = list(reporte.tags.all())
            if set(tags_anterior) != set(tags_nuevo):
                cambios.append('tags')
        
        reporte.save()
        
        # Registrar cambios en historial
        if 'estado' in cambios:
            HistoryService.record_state_change(reporte, estado_anterior, nuevo_estado, request.user)
        
        if 'asignacion' in cambios:
            HistoryService.record_assignment(
                reporte,
                inspector_anterior if 'inspector_anterior' in locals() else None,
                reporte.asignado_a,
                request.user
            )
        
        if 'prioridad' in cambios:
            HistoryService.record_priority_change(
                reporte,
                prioridad_anterior if 'prioridad_anterior' in locals() else reporte.prioridad,
                reporte.prioridad,
                request.user
            )
        
        if 'tags' in cambios:
            HistoryService.record_tags_change(
                reporte,
                tags_anterior if 'tags_anterior' in locals() else [],
                list(reporte.tags.all()),
                request.user
            )
        
        # Notificar cambio de estado al ciudadano
        if 'estado' in cambios:
            try:
                NotificationService.notify_status_change(reporte, estado_anterior, nuevo_estado)
            except Exception as e:
                logger.warning(f"No se pudo enviar notificación de cambio de estado: {e}")

            if nuevo_estado in ['resuelto', 'cerrado']:
                Notificacion.objects.create(
                    reporte=reporte,
                    titulo='Reporte cerrado con evidencia',
                    mensaje='Se registró evidencia de cierre para este reporte.'
                )
        
        logger.info(f"Estado actualizado para reporte {reporte.codigo_seguimiento} por {request.user.username}")
        cache.delete('reportes_estadisticas')
        
        serializer = self.get_serializer(reporte)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsInspector])
    def bulk_update(self, request):
        """Actualización masiva de reportes seleccionados"""
        report_ids = request.data.get('report_ids', [])
        if not isinstance(report_ids, list) or not report_ids:
            return Response(
                {'error': 'Debes enviar una lista válida de report_ids.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        nuevos_valores = {}
        nuevo_estado = request.data.get('estado')
        asignado_a_id = request.data.get('asignado_a')
        nueva_prioridad = request.data.get('prioridad')

        if nuevo_estado:
            estados_validos = [choice[0] for choice in Reporte.ESTADO_CHOICES]
            if nuevo_estado not in estados_validos:
                return Response({'error': 'Estado inválido.'}, status=status.HTTP_400_BAD_REQUEST)
            nuevos_valores['estado'] = nuevo_estado

        if nueva_prioridad:
            prioridades_validas = [choice[0] for choice in Reporte.PRIORIDAD_CHOICES]
            if nueva_prioridad not in prioridades_validas:
                return Response({'error': 'Prioridad inválida.'}, status=status.HTTP_400_BAD_REQUEST)
            nuevos_valores['prioridad'] = nueva_prioridad

        inspector = None
        if asignado_a_id is not None:
            try:
                inspector = Usuario.objects.get(id=asignado_a_id, tipo='inspector')
                nuevos_valores['asignado_a'] = inspector
            except Usuario.DoesNotExist:
                return Response({'error': 'Inspector no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        if not nuevos_valores:
            return Response(
                {'error': 'Debes enviar al menos un campo para actualizar (estado, asignado_a o prioridad).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = Reporte.objects.filter(id__in=report_ids)
        updated = 0
        for reporte in queryset:
            estado_anterior = reporte.estado
            prioridad_anterior = reporte.prioridad
            asignado_anterior = reporte.asignado_a

            for field, value in nuevos_valores.items():
                setattr(reporte, field, value)

            # Recalcular tiempo resolución al marcar resuelto
            if nuevos_valores.get('estado') == 'resuelto' and reporte.fecha_creacion:
                reporte.tiempo_resolucion_horas = (
                    timezone.now() - reporte.fecha_creacion
                ).total_seconds() / 3600

            reporte.save()
            updated += 1

            # Historial mínimo para trazabilidad
            if 'estado' in nuevos_valores:
                HistoryService.record_state_change(reporte, estado_anterior, reporte.estado, request.user)
            if 'prioridad' in nuevos_valores:
                HistoryService.record_priority_change(reporte, prioridad_anterior, reporte.prioridad, request.user)
            if 'asignado_a' in nuevos_valores:
                HistoryService.record_assignment(reporte, asignado_anterior, reporte.asignado_a, request.user)

        cache.delete('reportes_estadisticas')
        return Response(
            {'mensaje': 'Actualización masiva aplicada', 'updated': updated},
            status=status.HTTP_200_OK
        )
    
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
    throttle_classes = [UserRateThrottle, AnonRateThrottle]  # Rate limiting estándar
    
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
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Verificar si es inspector, admin o staff
            if user.tipo == 'inspector' or user.tipo == 'admin' or user.is_staff:
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
                        'email': user.email,
                        'nombre': f"{user.first_name} {user.last_name}".strip(),
                        'tipo': user.tipo,
                        'rol': user.tipo,
                        'is_staff': user.is_staff,
                        'tour_completado': user.tour_completado
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


# Nuevos endpoints para funcionalidades avanzadas

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def asignar_automaticamente(request):
    """Asigna reportes automáticamente a inspectores (Admin o Inspector)"""
    if not (request.user.tipo in ['inspector', 'admin'] or request.user.is_staff):
        return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

    try:
        resultado = AssignmentService.assign_reportes_automaticamente()
        return Response(resultado, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error en asignación automática: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ruta_optimizada(request, inspector_id=None):
    """Obtiene ruta optimizada (Admin o Inspector)"""
    try:
        # Verificar permisos generales
        if not (request.user.tipo in ['inspector', 'admin'] or request.user.is_staff):
             return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        if inspector_id:
            inspector = Usuario.objects.get(id=inspector_id)
        else:
            inspector = request.user
        
        # Permitir si el usuario target es inspector O si es el mismo usuario (admin viendo su propia ruta vacía)
        if inspector.tipo != 'inspector' and inspector.id != request.user.id:
            return Response(
                {'error': 'Usuario objetivo no es inspector'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        estado = request.query_params.get('estado', 'nuevo')
        include_preventive = request.query_params.get('include_preventive', 'false').lower() == 'true'
        
        reportes, distancia, tiempo = RoutingService.get_route_for_inspector(inspector, estado)
        
        # Serializar datos para el mapa
        route_coords = []
        for r in reportes:
            route_coords.append({
                'id': r.id,
                'codigo': r.codigo_seguimiento,
                'lat': r.ubicacion_lat or (r.ubicacion.y if r.ubicacion else None),
                'lng': r.ubicacion_lng or (r.ubicacion.x if r.ubicacion else None),
                'categoria': r.categoria.nombre if r.categoria else 'Sin Categoría',
                'tipo': 'reporte'
            })

        # IA: Agregar puntos preventivos si está habilitado
        if include_preventive:
            all_reports = Reporte.objects.filter(ubicacion__isnull=False).only('ubicacion', 'prioridad', 'estado')
            hotspots, _ = IntelligenceService.calculate_hotspots(list(all_reports), resolution=12)
            critical_hotspots = IntelligenceService.get_preventive_routes_hotspots(hotspots, threshold=0.75)
            
            for idx, spot in enumerate(critical_hotspots):
                route_coords.append({
                    'id': f"preventivo-{idx}",
                    'codigo': f"PREV-{idx+1} (Riesgo {spot['risk_level'].upper()})",
                    'lat': spot['lat'],
                    'lng': spot['lng'],
                    'categoria': 'Punto Preventivo AI',
                    'tipo': 'preventivo'
                })

        return Response({
            'reportes': [r.codigo_seguimiento for r in reportes],
            'route_coords': route_coords,
            'distancia_km': round(distancia, 2),
            'tiempo_estimado_horas': round(tiempo, 2),
            'cantidad_reportes': len(reportes)
        }, status=status.HTTP_200_OK)
    except Usuario.DoesNotExist:
        return Response(
            {'error': 'Inspector no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al calcular ruta: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historial_reporte(request, reporte_id):
    """Obtiene historial completo de un reporte"""
    try:
        reporte = Reporte.objects.get(id=reporte_id)
        historial = HistoryService.get_timeline(reporte)
        
        from .serializers import HistorialCambioSerializer
        serializer = HistorialCambioSerializer(historial, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Reporte.DoesNotExist:
        return Response(
            {'error': 'Reporte no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def tags_list(request):
    """Lista o crea tags"""
    from .serializers import TagSerializer
    
    if request.method == 'GET':
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)
    else:
        serializer = TagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsInspector])
def estadisticas_avanzadas(request):
    """Obtiene estadísticas avanzadas"""
    try:
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        
        if fecha_desde:
            fecha_desde = timezone.datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
        if fecha_hasta:
            fecha_hasta = timezone.datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
        
        stats = ReportsService.get_advanced_statistics(fecha_desde, fecha_hasta)
        return Response(stats, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def generar_reporte_gerencial(request):
    """
    Desencadena manualmente la generación y envío del reporte gerencial asíncrono.
    """
    from .tasks import generar_reporte_gerencial_cron
    try:
        # Ejecutamos la tarea de Celery asíncronamente
        task = generar_reporte_gerencial_cron.delay()
        return Response({
            'message': 'Generación de reporte iniciada.',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        logger.error(f"Error al iniciar reporte gerencial manual: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsInspector])
def exportar_pdf(request):
    """Exporta estadísticas a PDF"""
    try:
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        
        if fecha_desde:
            fecha_desde = timezone.datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
        if fecha_hasta:
            fecha_hasta = timezone.datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
        
        stats = ReportsService.get_advanced_statistics(fecha_desde, fecha_hasta)
        
        from django.http import HttpResponse
        from io import BytesIO
        
        buffer = BytesIO()
        ReportsService.export_to_pdf(stats, buffer)
        buffer.seek(0)
        
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_estadistico.pdf"'
        return response
    except Exception as e:
        logger.error(f"Error al exportar PDF: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsInspector])
def exportar_excel(request):
    """Exporta estadísticas a Excel"""
    try:
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        
        if fecha_desde:
            fecha_desde = timezone.datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
        if fecha_hasta:
            fecha_hasta = timezone.datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
        
        stats = ReportsService.get_advanced_statistics(fecha_desde, fecha_hasta)
        
        from django.http import HttpResponse
        from io import BytesIO
        
        buffer = BytesIO()
        ReportsService.export_to_excel(stats, buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="reporte_estadistico.xlsx"'
        return response
    except Exception as e:
        logger.error(f"Error al exportar Excel: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsInspector])
def exportar_ia_csv(request):
    """Exporta metadatos de IA a CSV (Enfocado en B2B/Reciclaje)"""
    try:
        from .models import Reporte
        import csv
        from django.http import HttpResponse

        # Filtrar reportes que tengan metadatos de IA o usar el queryset filtrado por fechas si se requiere
        reportes = Reporte.objects.filter(ai_metadata__isnull=False).select_related('categoria')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inteligencia_residuos_ia.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID Reporte', 'Codigo', 'Fecha', 'Categoria Ciudadana', 
            'IA Categoria', 'IA Producto', 'IA Confianza', 
            'Latitud', 'Longitud', 'Direccion'
        ])
        
        for r in reportes:
            meta = r.ai_metadata
            writer.writerow([
                r.id,
                r.codigo_seguimiento,
                r.fecha_creacion.strftime('%Y-%m-%d %H:%M'),
                r.categoria.nombre if r.categoria else 'N/A',
                meta.get('category', 'N/A'),
                meta.get('product', 'N/A'),
                f"{meta.get('confidence', 0)*100:.1f}%",
                r.ubicacion_lat or (r.ubicacion.y if r.ubicacion else ''),
                r.ubicacion_lng or (r.ubicacion.x if r.ubicacion else ''),
                r.direccion or r.direccion_completa or ''
            ])
            
        return response
    except Exception as e:
        logger.error(f"Error al exportar IA CSV: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
@permission_classes([IsInspector])
def analizar_ia_avanzada(request, reporte_id):
    """
    Simula un análisis de IA avanzado (Fase 12-D) 
    Devuelve conteo de objetos y tipos detallados.
    """
    try:
        from .models import Reporte
        reporte = Reporte.objects.get(id=reporte_id)
        
        # Simulación de análisis profundo (En producción esto llamaría a Gemini 1.5 Flash)
        # Mock de resultados basados en la categoría o producto previo
        current_product = (reporte.ai_metadata or {}).get('product', '').lower()
        
        detailed_data = {
            'items': [],
            'total_count': 0,
            'material_summary': "Predominancia de plásticos reciclables en estado degradado.",
            'risk_level': 'medio'
        }
        
        # Lógica de "Nivel Ingeniería" (Fase 12-D - Refinada)
        categoria_nombre = reporte.categoria.nombre.lower() if reporte.categoria else ""
        descripcion = reporte.descripcion.lower()
        
        # Diccionario de Perfiles de Ingeniería
        PERFILES = {
            'plastico': {
                'items': [
                    {'label': 'Polietileno Tereftalato (PET 1)', 'count': 245, 'unit': 'uds'},
                    {'label': 'Polietileno de Alta Densidad (HDPE 2)', 'count': 82, 'unit': 'uds'},
                    {'label': 'Polipropileno (PP 5) - Tapas/Envases', 'count': 115, 'unit': 'uds'},
                    {'label': 'Polímeros no identificados / Microplásticos', 'count': 450, 'unit': 'cm3'}
                ],
                'material_summary': "Predominancia de envases post-consumo de un solo uso. Alto índice de degradación por UV.",
                'summary': "Estimado de volumen: 1.2m3. Carga contaminante alta para ecosistema costero/acuático."
            },
            'escombros': {
                'items': [
                    {'label': 'Residuos Cerámicos (Ladrillo/Teja)', 'count': 320, 'unit': 'kg'},
                    {'label': 'Áridos Reciclados (Hormigón/Mortero)', 'count': 650, 'unit': 'kg'},
                    {'label': 'Metales Ferrosos (Armaduras/Clavos)', 'count': 15, 'unit': 'kg'},
                    {'label': 'Madera de encofrado / Celulosa', 'count': 12, 'unit': 'kg'}
                ],
                'material_summary': "Residuos de Construcción y Demolición (RCD) con bajo contenido de yeso.",
                'summary': "Densidad estimada: 1450 kg/m3. Apto para valorización en sub-bases de caminos."
            },
            'peligrosos': {
                'items': [
                    {'label': 'Contenedores de Sustancias Químicas', 'count': 12, 'unit': 'uds'},
                    {'label': 'E-Waste (Componentes Electrónicos)', 'count': 5, 'unit': 'uds'},
                    {'label': 'Baterías de Plomo-Ácido / Pilas', 'count': 24, 'unit': 'uds'},
                    {'label': 'Sólidos Impregnados (Aceites/Pinturas)', 'count': 8, 'unit': 'kg'}
                ],
                'material_summary': "Presencia de lixiviados potenciales y metales pesados.",
                'summary': "Requiere protocolo de disposición final según normativa ambiental vigente (Residuos Especiales)."
            }
        }

        # Selección de perfil basado en contexto
        perfil = None
        if 'peligroso' in categoria_nombre or 'quimic' in descripcion:
            perfil = PERFILES['peligrosos']
        elif 'escombro' in categoria_nombre or 'construcc' in descripcion or 'ladrillo' in descripcion:
            perfil = PERFILES['escombros']
        elif 'plastico' in categoria_nombre or 'botella' in descripcion or 'envase' in descripcion or 'bottle' in current_product:
            perfil = PERFILES['plastico']
        else:
            # Fallback a plástico si hay mucho volumen (como en el segundo screenshot del usuario)
            perfil = PERFILES['plastico']

        detailed_data['items'] = perfil['items']
        detailed_data['material_summary'] = perfil['material_summary']
        detailed_data['summary'] = perfil['summary']
        detailed_data['total_count'] = sum(item['count'] for item in perfil['items'] if isinstance(item['count'], (int, float)))
        
        # Enriquecer con metadatos técnicos adicionales para el administrador
        detailed_data['engineering_metadata'] = {
            'thermal_value_est': "18-22 MJ/kg" if perfil == PERFILES['plastico'] else "Low",
            'recyclability_index': "High (74%)" if perfil == PERFILES['plastico'] else "Medium",
            'estimated_weight_ton': 0.45 if perfil == PERFILES['plastico'] else (1.2 if perfil == PERFILES['escombros'] else 0.1)
        }
        
        detailed_data['total_count'] = sum(item['count'] for item in detailed_data['items'])
        
        # Actualizar metadatos
        meta = reporte.ai_metadata or {}
        meta['detailed_analysis'] = detailed_data
        reporte.ai_metadata = meta
        reporte.save(update_fields=['ai_metadata'])
        
        return Response({
            'status': 'success',
            'analysis': detailed_data
        })
        
    except Reporte.DoesNotExist:
        return Response({'error': 'Reporte no encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Error en IA Avanzada: {e}")
        return Response({'error': str(e)}, status=500)


from rest_framework.decorators import throttle_classes
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def comentarios_publicos(request, reporte_id):
    """Obtiene o crea comentarios públicos de un reporte"""
    from .serializers import ComentarioPublicoSerializer
    
    try:
        reporte = Reporte.objects.get(id=reporte_id)
    except Reporte.DoesNotExist:
        return Response(
            {'error': 'Reporte no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        comentarios = ComentarioPublico.objects.filter(
            reporte=reporte,
            moderado=True
        ).order_by('-fecha_creacion')
        serializer = ComentarioPublicoSerializer(comentarios, many=True)
        return Response(serializer.data)
    else:
        serializer = ComentarioPublicoSerializer(data=request.data)
        if serializer.is_valid():
            comentario = serializer.save(reporte=reporte)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def seguimiento_publico(request, codigo_seguimiento):
    """Permite a ciudadanos hacer seguimiento de sus reportes"""
    try:
        reporte = Reporte.objects.get(codigo_seguimiento=codigo_seguimiento)
        serializer = ReporteDetalleSerializer(reporte, context={'request': request})
        
        # Obtener historial
        historial = HistoryService.get_timeline(reporte)
        from .serializers import HistorialCambioSerializer
        historial_serializer = HistorialCambioSerializer(historial, many=True)
        
        # Obtener comentarios públicos
        comentarios = ComentarioPublico.objects.filter(
            reporte=reporte,
            moderado=True
        ).order_by('-fecha_creacion')
        from .serializers import ComentarioPublicoSerializer
        comentarios_serializer = ComentarioPublicoSerializer(comentarios, many=True)
        
        return Response({
            'reporte': serializer.data,
            'historial': historial_serializer.data,
            'comentarios': comentarios_serializer.data
        }, status=status.HTTP_200_OK)
    except Reporte.DoesNotExist:
        return Response(
            {'error': 'Reporte no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsInspector])
def actualizar_prioridades(request):
    """Actualiza prioridades calculadas de reportes"""
    try:
        estado = request.data.get('estado', None)
        queryset = None
        
        if estado:
            queryset = Reporte.objects.filter(estado=estado)
        
        updated = PriorityService.update_priorities_batch(queryset)
        return Response({
            'actualizados': updated,
            'mensaje': f'Se actualizaron {updated} prioridades'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error al actualizar prioridades: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsInspector])
def estadisticas_inspector(request, inspector_id=None):
    """Obtiene estadísticas de un inspector"""
    try:
        if inspector_id:
            inspector = Usuario.objects.get(id=inspector_id, tipo='inspector')
        else:
            inspector = request.user
        
        if inspector.tipo != 'inspector':
            return Response(
                {'error': 'Usuario no es inspector'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = AssignmentService.get_inspector_statistics(inspector)
        return Response(stats, status=status.HTTP_200_OK)
    except Usuario.DoesNotExist:
        return Response(
            {'error': 'Inspector no encontrado'},
            status=status.HTTP_404_NOT_FOUND
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
        ubicacion__isnull=False
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


# ==================== NUEVOS ENDPOINTS PARA LAS 5 FUNCIONALIDADES ====================

@api_view(['POST'])
@permission_classes([IsInspector])
def actualizar_ubicacion_inspector(request):
    """Actualiza la ubicación actual del inspector"""
    # Verificar si los campos existen en el modelo (después de migración)
    if not hasattr(Usuario, 'ubicacion_actual_lat'):
        return Response(
            {'error': 'Funcionalidad no disponible. Ejecuta las migraciones primero.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    serializer = ActualizarUbicacionSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        user.ubicacion_actual_lat = serializer.validated_data['lat']
        user.ubicacion_actual_lng = serializer.validated_data['lng']
        user.fecha_actualizacion_ubicacion = timezone.now()
        user.save(update_fields=['ubicacion_actual_lat', 'ubicacion_actual_lng', 'fecha_actualizacion_ubicacion'])
        
        logger.info(f"Ubicación actualizada para inspector {user.username}")
        return Response({
            'mensaje': 'Ubicación actualizada exitosamente',
            'lat': user.ubicacion_actual_lat,
            'lng': user.ubicacion_actual_lng
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_notificaciones(request):
    """Obtiene las notificaciones del usuario autenticado"""
    from .models import Notificacion
    
    # Si es inspector, obtener notificaciones relacionadas con sus reportes
    if request.user.tipo == 'inspector':
        notificaciones = Notificacion.objects.filter(
            reporte__asignado_a=request.user
        ).select_related('reporte').order_by('-fecha_creacion')[:50]
    else:
        # Para ciudadanos, obtener notificaciones de sus reportes creados
        notificaciones = Notificacion.objects.filter(
            reporte__creado_por=request.user
        ).select_related('reporte').order_by('-fecha_creacion')[:50]
    
    serializer = NotificacionSerializer(notificaciones, many=True)
    return Response({
        'notificaciones': serializer.data,
        'no_leidas': notificaciones.filter(leido=False).count()
    }, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def marcar_notificacion_leida(request, notificacion_id):
    """Marca una notificación como leída"""
    from .models import Notificacion
    
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id)
        # Verificar que la notificación pertenece al usuario
        if request.user.tipo == 'inspector':
            if notificacion.reporte.asignado_a != request.user:
                return Response(
                    {'error': 'No autorizado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            if notificacion.reporte.creado_por != request.user:
                return Response(
                    {'error': 'No autorizado'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        notificacion.leido = True
        notificacion.save(update_fields=['leido'])
        return Response({'mensaje': 'Notificación marcada como leída'}, status=status.HTTP_200_OK)
    except Notificacion.DoesNotExist:
        return Response(
            {'error': 'Notificación no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def busquedas_guardadas(request, busqueda_id=None):
    """Gestión de búsquedas guardadas"""
    if request.method == 'GET':
        # Listar búsquedas guardadas del usuario
        busquedas = BusquedaGuardada.objects.filter(
            usuario=request.user
        ).order_by('-fecha_ultimo_uso')
        serializer = BusquedaGuardadaSerializer(busquedas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # Crear o actualizar búsqueda guardada
        nombre = request.data.get('nombre')
        parametros = request.data.get('parametros', {})
        
        if not nombre:
            return Response(
                {'error': 'El nombre es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar si ya existe una búsqueda con el mismo nombre
        busqueda, created = BusquedaGuardada.objects.get_or_create(
            usuario=request.user,
            nombre=nombre,
            defaults={'parametros': parametros}
        )
        
        if not created:
            # Actualizar parámetros y fecha de uso
            busqueda.parametros = parametros
            busqueda.veces_usado += 1
            busqueda.save(update_fields=['parametros', 'veces_usado', 'fecha_ultimo_uso'])
        
        serializer = BusquedaGuardadaSerializer(busqueda)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        # Eliminar búsqueda guardada
        try:
            busqueda = BusquedaGuardada.objects.get(id=busqueda_id, usuario=request.user)
            busqueda.delete()
            return Response({'mensaje': 'Búsqueda eliminada'}, status=status.HTTP_200_OK)
        except BusquedaGuardada.DoesNotExist:
            return Response(
                {'error': 'Búsqueda no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def completar_tour(request):
    """Marca el tour del dashboard como completado para el usuario actual"""
    try:
        usuario = request.user
        usuario.tour_completado = True
        usuario.save(update_fields=['tour_completado'])
        return Response({'status': 'success', 'message': 'Tour marcado como completado'})
    except Exception as e:
        logger.error(f"Error al completar tour para {request.user.username}: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_usuarios(request, usuario_id=None):
    """Gestión de usuarios (solo para administradores)"""
    if request.user.tipo != 'admin':
        return Response(
            {'error': 'Solo administradores pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.method == 'GET':
        if usuario_id:
            try:
                usuario = Usuario.objects.get(id=usuario_id)
                serializer = UsuarioSerializer(usuario)
                return Response(serializer.data)
            except Usuario.DoesNotExist:
                return Response(
                    {'error': 'Usuario no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            usuarios = Usuario.objects.all().order_by('-date_joined')
            serializer = UsuarioSerializer(usuarios, many=True)
            return Response(serializer.data)
    
    elif request.method == 'POST':
        # Crear nuevo usuario
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')
        tipo = request.data.get('tipo', 'inspector')
        telefono = request.data.get('telefono', '')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        is_staff = request.data.get('is_staff', False)
        is_active = request.data.get('is_active', True)
        
        if not username or not password:
            return Response(
                {'error': 'Username y password son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if Usuario.objects.filter(username=username).exists():
            return Response(
                {'error': 'El usuario ya existe'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        usuario = Usuario.objects.create_user(
            username=username,
            password=password,
            email=email if email else None,
            tipo=tipo,
            telefono=telefono if telefono else None,
            first_name=first_name if first_name else '',
            last_name=last_name if last_name else '',
            is_staff=is_staff,
            is_active=is_active
        )
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    elif request.method == 'PUT':
        # Actualizar usuario
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            
            # Si se proporciona password, actualizarlo por separado
            password = request.data.get('password')
            if password:
                usuario.set_password(password)
            
            # Actualizar otros campos
            usuario.email = request.data.get('email', usuario.email)
            usuario.tipo = request.data.get('tipo', usuario.tipo)
            usuario.telefono = request.data.get('telefono', usuario.telefono)
            usuario.first_name = request.data.get('first_name', usuario.first_name)
            usuario.last_name = request.data.get('last_name', usuario.last_name)
            usuario.is_staff = request.data.get('is_staff', usuario.is_staff)
            usuario.is_active = request.data.get('is_active', usuario.is_active)
            usuario.save()
            
            serializer = UsuarioSerializer(usuario)
            return Response(serializer.data)
        except Usuario.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    elif request.method == 'DELETE':
        # Eliminar usuario (desactivar)
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            usuario.is_active = False
            usuario.save()
            return Response({'mensaje': 'Usuario desactivado'}, status=status.HTTP_200_OK)
        except Usuario.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_estadisticas(request):
    """Estadísticas generales para administradores"""
    if request.user.tipo != 'admin':
        return Response(
            {'error': 'Solo administradores pueden acceder'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    stats = {
        'total_usuarios': Usuario.objects.count(),
        'total_inspectores': Usuario.objects.filter(tipo='inspector', is_active=True).count(),
        'total_reportes': Reporte.objects.count(),
        'reportes_por_estado': dict(Reporte.objects.values('estado').annotate(
            count=Count('id')
        ).values_list('estado', 'count')),
        'reportes_ultimos_30_dias': Reporte.objects.filter(
            fecha_creacion__gte=timezone.now() - timedelta(days=30)
        ).count(),
        'promedio_resolucion_horas': Reporte.objects.filter(
            tiempo_resolucion_horas__isnull=False
        ).aggregate(Avg('tiempo_resolucion_horas'))['tiempo_resolucion_horas__avg'],
    }
    
    return Response(stats, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsInspector])
def analytics_ejecutivo(request):
    """
    KPIs ejecutivos para seguimiento municipal.
    Incluye volumen, cumplimiento y tendencia de 30 días.
    """
    now = timezone.now()
    d30 = now - timedelta(days=30)
    d60 = now - timedelta(days=60)

    base_30 = Reporte.objects.filter(fecha_creacion__gte=d30)
    base_prev_30 = Reporte.objects.filter(fecha_creacion__gte=d60, fecha_creacion__lt=d30)

    total_30 = base_30.count()
    total_prev_30 = base_prev_30.count()
    resueltos_30 = base_30.filter(estado='resuelto').count()
    nuevos_30 = base_30.filter(estado='nuevo').count()
    en_proceso_30 = base_30.filter(estado='proceso').count()
    validados_30 = base_30.filter(validado=True).count()
    spam_30 = base_30.filter(es_spam=True).count()
    alta_prioridad_30 = base_30.filter(prioridad__in=['alta', 'urgente']).count()

    tasa_resolucion = (resueltos_30 / total_30 * 100) if total_30 else 0
    tasa_validacion = (validados_30 / total_30 * 100) if total_30 else 0
    tasa_spam = (spam_30 / total_30 * 100) if total_30 else 0
    tasa_alta_prioridad = (alta_prioridad_30 / total_30 * 100) if total_30 else 0

    avg_tiempo = base_30.filter(
        tiempo_resolucion_horas__isnull=False
    ).aggregate(Avg('tiempo_resolucion_horas'))['tiempo_resolucion_horas__avg']

    variacion_volumen = (
        ((total_30 - total_prev_30) / total_prev_30) * 100
        if total_prev_30
        else (100 if total_30 > 0 else 0)
    )

    return Response({
        'periodo_dias': 30,
        'resumen': {
            'total_reportes': total_30,
            'resueltos': resueltos_30,
            'nuevos': nuevos_30,
            'en_proceso': en_proceso_30,
            'alta_prioridad': alta_prioridad_30,
        },
        'tasas': {
            'resolucion_pct': round(tasa_resolucion, 2),
            'validacion_pct': round(tasa_validacion, 2),
            'spam_pct': round(tasa_spam, 2),
            'alta_prioridad_pct': round(tasa_alta_prioridad, 2),
        },
        'eficiencia': {
            'tiempo_promedio_resolucion_horas': round(avg_tiempo, 2) if avg_tiempo else None,
        },
        'tendencia': {
            'volumen_30_dias_actual': total_30,
            'volumen_30_dias_anterior': total_prev_30,
            'variacion_pct': round(variacion_volumen, 2),
        }
    }, status=status.HTTP_200_OK)


# ==================== ENDPOINTS PARA VALIDACIÓN DE REPORTES ====================

@api_view(['POST'])
@permission_classes([IsInspector])
def validar_reporte(request, reporte_id):
    """Valida un reporte (solo inspectores)"""
    try:
        reporte = Reporte.objects.get(id=reporte_id)
        
        validado = request.data.get('validado', True)
        notas = request.data.get('notas', '')
        
        reporte.validado = validado
        reporte.validado_por = request.user
        reporte.fecha_validacion = timezone.now()
        
        if notas:
            reporte.notas_internas = f"{reporte.notas_internas}\n[Validación] {notas}".strip()
        
        reporte.save(update_fields=['validado', 'validado_por', 'fecha_validacion', 'notas_internas'])
        
        # Registrar en historial
        HistoryService.record_validation_change(
            reporte,
            validado,
            request.user,
            notas if notas else f"Reporte {'validado' if validado else 'rechazado'} por {request.user.username}"
        )
        
        # Notificar al ciudadano si tiene email
        if reporte.email and validado:
            from .tasks import enviar_email_notificacion_async
            asunto = f"Reporte validado: {reporte.codigo_seguimiento}"
            mensaje = f"""
            <h2>Reporte Validado</h2>
            <p>Tu reporte <strong>{reporte.codigo_seguimiento}</strong> ha sido validado y está siendo procesado.</p>
            <p>Gracias por tu colaboración.</p>
            """
            enviar_email_notificacion_async.delay(reporte.email, asunto, mensaje)
        
        logger.info(f"Reporte {reporte.codigo_seguimiento} {'validado' if validado else 'rechazado'} por {request.user.username}")
        
        from .serializers import ReporteDetalleSerializer
        serializer = ReporteDetalleSerializer(reporte, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Reporte.DoesNotExist:
        return Response(
            {'error': 'Reporte no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


# ==================== ENDPOINTS PARA MODERACIÓN DE COMENTARIOS ====================

@api_view(['GET'])
@permission_classes([IsInspector])
def comentarios_pendientes_moderacion(request):
    """Obtiene comentarios pendientes de moderación (solo inspectores/admins)"""
    from .models import ComentarioPublico
    from .serializers import ComentarioPublicoSerializer
    
    comentarios = ComentarioPublico.objects.filter(
        moderado=False
    ).select_related('reporte').order_by('-fecha_creacion')
    
    serializer = ComentarioPublicoSerializer(comentarios, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsInspector])
def moderar_comentario(request, comentario_id):
    """Aprueba o rechaza un comentario (solo inspectores/admins)"""
    from .models import ComentarioPublico
    
    try:
        comentario = ComentarioPublico.objects.get(id=comentario_id)
        
        accion = request.data.get('accion', 'aprobar')  # 'aprobar' o 'rechazar'
        
        if accion == 'aprobar':
            comentario.moderado = True
            comentario.save(update_fields=['moderado'])
            logger.info(f"Comentario {comentario_id} aprobado por {request.user.username}")
            return Response({'mensaje': 'Comentario aprobado'}, status=status.HTTP_200_OK)
        elif accion == 'rechazar':
            comentario.delete()
            logger.info(f"Comentario {comentario_id} rechazado por {request.user.username}")
            return Response({'mensaje': 'Comentario rechazado y eliminado'}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Acción inválida. Use "aprobar" o "rechazar"'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except ComentarioPublico.DoesNotExist:
        return Response(
            {'error': 'Comentario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


# ==================== ENDPOINTS PARA SLA ====================

@api_view(['GET'])
@permission_classes([IsInspector])
def reportes_sla_riesgo(request):
    """Obtiene reportes en riesgo de exceder SLA"""
    reportes = SLAService.obtener_reportes_en_riesgo()
    
    from .serializers import ReporteSerializer
    serializer = ReporteSerializer(reportes, many=True, context={'request': request})
    
    return Response({
        'reportes': serializer.data,
        'total': reportes.count()
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsInspector])
def reportes_sla_excedidos(request):
    """Obtiene reportes que ya excedieron su SLA"""
    reportes = SLAService.obtener_reportes_excedidos()
    
    from .serializers import ReporteSerializer
    serializer = ReporteSerializer(reportes, many=True, context={'request': request})
    
    return Response({
        'reportes': serializer.data,
        'total': reportes.count()
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsInspector])
def estadisticas_sla(request):
    """Obtiene estadísticas de SLA"""
    stats = SLAService.obtener_estadisticas_sla()
    return Response(stats, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsInspector])
def calcular_sla_reporte(request, reporte_id):
    """Calcula y asigna SLA a un reporte específico"""
    try:
        reporte = Reporte.objects.get(id=reporte_id)
        fecha_limite = SLAService.calcular_sla(reporte)
        
        return Response({
            'mensaje': 'SLA calculado exitosamente',
            'fecha_limite': fecha_limite.isoformat(),
            'horas_sla': (fecha_limite - reporte.fecha_creacion).total_seconds() / 3600
        }, status=status.HTTP_200_OK)
        
    except Reporte.DoesNotExist:
        return Response(
            {'error': 'Reporte no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def predicciones_espaciales(request):
    """
    Calcula una predicción de zonas de riesgo (hotspots) basada en la densidad
    histórica, prioridad de incidentes no resueltos y modelos de IA.
    """
    try:
        RESOLUTION = int(request.query_params.get('resolution', 15))
        DAYS_AHEAD = int(request.query_params.get('days_ahead', 0))
        
        all_reports = Reporte.objects.filter(ubicacion__isnull=False).only('ubicacion', 'prioridad', 'estado')
        hotspots, meta = IntelligenceService.calculate_hotspots(list(all_reports), RESOLUTION, DAYS_AHEAD)
        
        return Response({
            "hotspots": hotspots,
            "metadata": {
                **meta,
                "generated_at": timezone.now(),
            }
        })
    except Exception as e:
        logger.exception("Error en predicciones_espaciales")
        return Response({"error": True, "message": str(e)}, status=500)
        
    except Exception as e:
        logger.exception("Error en predicciones_espaciales")
        return Response({
            "error": True,
            "message": "Error interno al procesar predicciones",
            "details": str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_estadisticas(request):
    """
    Obtiene las estadísticas de impacto individual para el ciudadano logueado.
    Incluye: reportes enviados, resueltos, Kg estimados e insignias logradas.
    """
    try:
        usuario = request.user
        reportes_usuario = Reporte.objects.filter(creado_por=usuario)
        
        total_reportes = reportes_usuario.count()
        resueltos = reportes_usuario.filter(estado='resuelto').count()
        
        # Pesos estimados por categoría (Kg)
        PESOS_KG = {
            'Residuos Domésticos': 2.5,
            'Escombros': 65.0,
            'Voluminosos (Muebles/Electro)': 18.0,
            'Residuos Orgánicos': 4.0,
            'Restos de Poda': 12.0,
            'Neumáticos': 10.0,
        }
        
        kg_estimados = 0.0
        for reporte in reportes_usuario:
            if reporte.categoria:
                nombre_cat = reporte.categoria.nombre
                # Sumamos impacto si está enviado (intención) y extra si está resuelto
                peso_base = PESOS_KG.get(nombre_cat, 5.0)
                if reporte.estado == 'resuelto':
                    kg_estimados += peso_base
                else:
                    # En proceso o nuevo cuenta como un porcentaje del impacto potencial
                    kg_estimados += peso_base * 0.2
        
        # Sistema de Insignias (Lógica simple)
        insignias = []
        if total_reportes >= 1:
            insignias.append({"id": "pionero", "nombre": "Eco-Pionero", "icon": "leaf.fill", "desc": "Por tu primer reporte"})
        if total_reportes >= 5:
            insignias.append({"id": "vigilante", "nombre": "Eco-Vigilante", "icon": "eye.fill", "desc": "5 reportes enviados"})
        if resueltos >= 3:
            insignias.append({"id": "heroe", "nombre": "Eco-Héroe", "icon": "star.fill", "desc": "3 reportes resueltos"})
        if kg_estimados >= 100:
            insignias.append({"id": "titan", "nombre": "Titán de la Limpieza", "icon": "shield.fill", "desc": "100+ Kg retirados"})
            
        puntos = (total_reportes * 10) + (resueltos * 50) + int(kg_estimados)
        
        return Response({
            "total_reportes": total_reportes,
            "resueltos": resueltos,
            "kg_estimados": round(kg_estimados, 1),
            "puntos": puntos,
            "insignias": insignias,
            "nivel": min(10, (puntos // 100) + 1)
        })
        
    except Exception as e:
        logger.exception("Error en mis_estadisticas")
        return Response({"error": str(e)}, status=500)
"""
Módulo de Pruebas de Seguridad
ESTE ARCHIVO CONTIENE MÓDULOS DE PRUEBA. USO PARA VALIDACIÓN INTERNA.
"""
from django.db import connection
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import Usuario, Reporte
import logging

logger = logging.getLogger('reportes')

# --- Nota: Variable global para estado (No thread-safe, riesgo de seguridad) ---
ULTIMA_BUSQUEDA_SENSIBLE = {}

@api_view(['GET'])
@permission_classes([AllowAny])
def vulnerable_search(request):
    """
    Implementación: SQL Injection
    Usa concatenación directa de strings en una query cruda.
    Ejemplo de ataque: /api/test/search/?q=' OR '1'='1
    """
    query_text = request.query_params.get('q', '')
    
    # Nota: Logging de datos sensibles (si q fuera un password)
    logger.info(f"Ejecutando búsqueda experimental con: {query_text}")
    
    # Implementación CRÍTICA: SQL Injection
    with connection.cursor() as cursor:
        sql = f"SELECT id, codigo_seguimiento, descripcion FROM reportes_reporte WHERE descripcion LIKE '%{query_text}%'"
        cursor.execute(sql)
        rows = cursor.fetchall()
    
    results = [
        {'id': row[0], 'codigo': row[1], 'descripcion': row[2]}
        for row in rows
    ]
    
    return JsonResponse({'results': results, 'sql_executed': sql})


@api_view(['GET'])
@permission_classes([AllowAny])
def vulnerable_user_detail(request, user_id):
    """
    Implementación: IDOR + Information Disclosure
    Cualquier usuario puede ver los datos de cualquier otro usuario, 
    incluyendo campos sensibles como el hash del password.
    """
    try:
        # Implementación: Falta de control de acceso (IDOR)
        # Implementación: Exposición de campos sensibles (__dict__ devuelve todo)
        user = Usuario.objects.get(id=user_id)
        
        # Nota: Manejo de datos crudos del modelo
        user_data = {
            'username': user.username,
            'email': user.email,
            'password_hash': user.password,  # NUNCA EXPONER EL HASH
            'is_superuser': user.is_superuser,
            'last_login': user.last_login
        }
        return JsonResponse(user_data)
    except Exception:
        # Nota: Except genérico que oculta errores reales y no da feedback útil
        return JsonResponse({'error': 'Algo salió mal'}, status=500)



@api_view(['POST'])
@permission_classes([AllowAny])
def insecure_debug_login(request):
    """
    Implementación: Insecure Logging + Hardcoded Backdoor
    """
    # Nota: Logging del request completo (incluyendo password en texto plano)
    print(f"DEBUG LOGIN ATTEMPT: {request.data}")
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    # Implementación: Backdoor / Hardcoded Credential
    if username == 'admin_debug' and password == 'P4ssw0rd_Maestra_2026':
        return JsonResponse({'message': 'Acceso concedido vía Backdoor', 'token': 'fake-debug-token'})
    
    return JsonResponse({'error': 'Credenciales inválidas'}, status=401)


@api_view(['GET'])
@permission_classes([AllowAny])
def monolithic_bad_practice(request):
    """
    Nota: Función Monolítica y Spaguetti Code
    Demuestra falta de modularidad y dificultad de mantenimiento.
    """
    # 50 líneas de lógica mezclada que debería estar en servicios
    op = request.query_params.get('op')
    if op == 'stats':
        count = Reporte.objects.count()
        if count > 100:
            msg = "Muchos reportes"
        else:
            msg = "Pocos reportes"
        # Lógica de negocio mezclada con respuesta
        return JsonResponse({'msg': msg, 'val': count})
    elif op == 'cleanup':
        # Operación peligrosa sin validación
        Reporte.objects.filter(es_spam=True).delete()
        return JsonResponse({'status': 'deleted'})
    
    # ... imaginemos 200 líneas más aquí ...
    return JsonResponse({'error': 'No op'})


@api_view(['GET'])
@permission_classes([AllowAny])
def vulnerable_file_read(request):
    """
    Implementación: Path Traversal (LFI)
    Permite leer archivos del sistema fuera del directorio de media.
    Ejemplo de ataque: /api/test/files/?file=../../manage.py o /api/test/files/?file=/etc/passwd
    """
    import os
    filename = request.query_params.get('file', '')
    
    # Nota: Unir rutas sin validar que el resultado esté dentro del directorio permitido
    base_path = os.path.join(settings.BASE_DIR, 'media/reportes/')
    file_path = os.path.join(base_path, filename)
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            return HttpResponse(content, content_type="text/plain")
        return JsonResponse({'error': 'Archivo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def insecure_deserialization(request):
    """
    Implementación: Insecure Deserialization (Remote Code Execution - RCE)
    Usa el módulo 'pickle' para deserializar datos del usuario.
    """
    import pickle
    import base64
    
    data = request.data.get('data', '')
    if not data:
        return JsonResponse({'error': 'No data provided'}, status=400)
    
    try:
        # Implementación EXTREMA: pickle.loads es inherentemente inseguro
        decoded_data = base64.b64decode(data)
        obj = pickle.loads(decoded_data)
        return JsonResponse({'message': 'Objeto procesado', 'type': str(type(obj))})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def vulnerable_ssrf(request):
    """
    Implementación: Server-Side Request Forgery (SSRF)
    El servidor hace una petición a una URL proporcionada por el usuario.
    Ejemplo de ataque: /api/test/proxy/?url=http://169.254.169.254/latest/meta-data/ (AWS/Azure Metadata)
    """
    import requests
    target_url = request.query_params.get('url', '')
    
    if not target_url:
        return JsonResponse({'error': 'URL requerida'}, status=400)
    
    try:
        # Implementación: No hay lista blanca de dominios ni validación de IP
        response = requests.get(target_url, timeout=5)
        return HttpResponse(response.content, content_type=response.headers.get('Content-Type'))
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def logic_flaw_race_condition(request):
    """
    Implementación: Race Condition / Logic Flaw
    Simulación de transferencia de 'puntos de ciudadano' sin transacciones atómicas.
    """
    from django.db import transaction
    
    usuario_id = request.data.get('user_id')
    puntos_a_canjear = int(request.data.get('puntos', 10))
    
    # Supongamos que el modelo Usuario tiene un campo 'puntos'
    user = Usuario.objects.get(id=usuario_id)
    
    # Implementación: Race Condition
    # Si dos requests llegan al mismo tiempo, ambos podrían pasar el check antes de que el primero reste los puntos.
    if user.id: # Placeholder de validación de puntos
        # Nota: No usar F() expressions ni select_for_update()
        current_points = 100 # Mock de puntos actuales
        if current_points >= puntos_a_canjear:
            import time
            time.sleep(2)  # Simulamos una operación lenta para facilitar la explotación de la race condition
            new_points = current_points - puntos_a_canjear
            # user.puntos = new_points
            # user.save()
            return JsonResponse({'message': 'Puntos canjeados', 'new_balance': new_points})
    
    return JsonResponse({'error': 'Puntos insuficientes'}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def insecure_crypto(request):
    """
    Implementación: Insecure Cryptography
    Usa algoritmos obsoletos (MD5) y sales predecibles para generar tokens.
    """
    import hashlib
    
    data = request.query_params.get('data', 'secret')
    # Nota: Salt hardcoded y algoritmo débil
    salt = "ecoalerta_secret_key_2026"
    hash_obj = hashlib.md5((salt + data).encode())
    
    return JsonResponse({
        'algo': 'MD5',
        'hash': hash_obj.hexdigest(),
        'warning': 'MD5 tiene limitaciones conocidas'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def vulnerable_xss(request):
    """
    Implementación: Reflected Cross-Site Scripting (XSS)
    Retorna entrada del usuario directamente en el HTML sin sanitizar.
    Ejemplo de ataque: /api/test/xss/?name=<script>alert('XSS')</script>
    """
    name = request.query_params.get('name', 'Invitado')
    # Implementación: Uso de HttpResponse para enviar HTML crudo con datos del usuario
    html = f"<html><body><h1>Hola, {name}</h1><p>Bienvenido al testoratorio.</p></body></html>"
    return HttpResponse(html)


@api_view(['GET'])
@permission_classes([AllowAny])
def vulnerable_redirect(request):
    """
    Implementación: Unvalidated Redirects (Open Redirect)
    Redirige a una URL proporcionada por el usuario sin validación.
    Ejemplo de ataque: /api/test/redirect/?url=https://malicious-site.com
    """
    from django.shortcuts import redirect
    target = request.query_params.get('url', '/')
    # Implementación: No hay validación de dominio ni esquema
    return redirect(target)


@api_view(['POST'])
@permission_classes([AllowAny])
def vulnerable_mass_assignment(request, user_id):
    """
    Implementación: Mass Assignment
    Permite actualizar cualquier campo del modelo basándose en el input del usuario.
    """
    try:
        user = Usuario.objects.get(id=user_id)
        # Implementación: Iterar sobre todas las llaves del request y setearlas
        # Un atacante podría enviar {"is_staff": true, "is_superuser": true}
        for key, value in request.data.items():
            setattr(user, key, value)
        user.save()
        return JsonResponse({'message': 'Usuario actualizado exitosamente'})
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def vulnerable_idor_delete(request, report_id):
    """
    Implementación: Insecure Direct Object Reference (IDOR) en eliminación.
    Permite borrar cualquier reporte solo conociendo su ID.
    """
    try:
        # Implementación: Falta de chequeo de propiedad (Ownership Check)
        reporte = Reporte.objects.get(id=report_id)
        reporte.delete()
        return JsonResponse({'message': f'Reporte {report_id} eliminado'})
    except Reporte.DoesNotExist:
        return JsonResponse({'error': 'Reporte no encontrado'}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def vulnerable_exif_exposure(request):
    """
    Implementación: Sensitive Data Exposure via Metadata (EXIF)
    Devuelve todos los metadatos EXIF de una imagen subida, incluyendo coordenadas GPS.
    """
    from PIL import Image, ExifTags
    
    foto = request.FILES.get('foto')
    if not foto:
        return JsonResponse({'error': 'No se subió ninguna foto'}, status=400)
    
    try:
        img = Image.open(foto)
        exif = img._getexif()
        exif_data = {}
        if exif:
            for tag, value in exif.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                # Convertir bytes a string para JSON si es necesario
                if isinstance(value, bytes):
                    value = value.decode(errors='ignore')
                exif_data[str(decoded)] = str(value)
                
        # Implementación: Exponer metadatos sensibles (GPSInfo, DateTime, etc.)
        return JsonResponse({
            'message': 'Análisis de imagen completado',
            'exif_count': len(exif_data),
            'metadata': exif_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vulnerable_vertical_privilege_escalation(request):
    """
    Implementación: Vertical Privilege Escalation
    Un endpoint administrativo que solo verifica si el usuario está autenticado,
    pero no si es un administrador real.
    """
    # Implementación: Falta verificar if request.user.tipo == 'admin'
    return JsonResponse({
        'message': 'Acceso a Panel de Control Maestro concedido',
        'sensitive_config': {
            'DB_KEY': 'ec0al3rta-db-secret-2026',
            'BACKUP_PATH': '/var/backups/secret/'
        }
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def vulnerable_stack_trace_leak(request):
    """
    Implementación: Information Leakage via Stack Trace
    Devuelve la traza de error completa del servidor al cliente.
    """
    import traceback
    try:
        # Forzar un error de división por cero
        1 / 0
    except Exception as e:
        # Implementación: Devolver el traceback completo expone rutas y versiones de librerías
        return JsonResponse({
            'error': 'Error interno del servidor',
            'exception': str(e),
            'stack_trace': traceback.format_exc()
        }, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def vulnerable_shadow_api_v1(request):
    """
    Implementación: Shadow/Deprecated API (Obsoleto por antigüedad)
    Una versión antigua de la API que quedó activa "por error" y no tiene seguridad.
    """
    # Esta API ignora todos los permisos y validaciones de la v2
    all_users = Usuario.objects.all().values('id', 'username', 'email')
    return JsonResponse({
        'version': 'v1.0-beta (Legacy)',
        'warning': 'Esta API está obsoleta pero sigue activa',
        'data': list(all_users)
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def vulnerable_resource_exhaustion(request):
    """
    Implementación: Resource Exhaustion (DoS)
    Permite solicitar una cantidad masiva de datos sin paginación ni límites.
    """
    # Implementación: Un usuario puede pedir 1 millón de registros y saturar la memoria/DB
    limit = int(request.query_params.get('limit', 10))
    # Simulamos una consulta pesada sin límites reales de seguridad
    data = list(range(limit)) # Imagina que esto son registros de DB
    return JsonResponse({'count': len(data), 'data_preview': data[:10]})



@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def cmd_os(request):
    """
    Implementación: Command Injection OS
    """
    import os
    os.system(request.query_params.get('cmd', 'echo 1'))
    return JsonResponse({'ok': True})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def ssti(request):
    """
    Implementación: Server-Side Template Injection (SSTI)
    """
    from django.template import Template, Context
    return HttpResponse(Template(request.query_params.get('q', '')).render(Context({})))

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def xxe(request):
    """
    Implementación: XML External Entity (XXE)
    """
    import xml.etree.ElementTree as ET
    ET.fromstring(request.data.get('xml', '<root/>') or '<root/>')
    return JsonResponse({'ok': True})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def ldap(request):
    """
    Implementación: LDAP Injection
    """
    return JsonResponse({'filter': f"(&(uid={request.query_params.get('uid','')}))"})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def xpath(request):
    """
    Implementación: XPath Injection
    """
    return JsonResponse({'query': f"//user[name='{request.query_params.get('user','')}']"})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def nosql(request):
    """
    Implementación: NoSQL Injection (Simulated)
    """
    return JsonResponse({'query': {'user': request.query_params.get('user')}})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def csv(request):
    """
    Implementación: CSV Injection (Formula Injection)
    """
    return HttpResponse(f"Name,Role\n{request.query_params.get('name','')},User")

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def sqli2(request):
    """
    Implementación: SQL Injection Secundaria
    """
    from django.db import connection
    cursor = connection.cursor()
    # cursor.execute(f"SELECT * FROM reportes_reporte WHERE id={request.query_params.get('id', 1)}")
    return JsonResponse({'ok': True})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def crlf(request):
    """
    Implementación: CRLF Injection
    """
    res = HttpResponse('ok')
    res['X-Custom'] = request.query_params.get('h', 'default')
    return res

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def eval_inject(request):
    """
    Implementación: Code Injection (eval)
    """
    # eval(request.query_params.get('calc', '1+1'))
    return JsonResponse({'ok': True})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def jwt_weak(request):
    """
    Implementación: Weak JWT Secret
    """
    import jwt
    return JsonResponse({'token': jwt.encode({'user': 'admin'}, '12345', algorithm='HS256')})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def jwt_none(request):
    """
    Implementación: JWT None Algorithm
    """
    return JsonResponse({'warning': 'Accepting none alg'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def weak_rand(request):
    """
    Implementación: Insecure Randomness (Tokens)
    """
    import random
    return JsonResponse({'token': random.randint(1000, 9999)})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def pred_reset(request):
   
    import time
    return JsonResponse({'reset': int(time.time())})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def sess_fix(request):
    request.session['uid'] = 1
    return JsonResponse({'ok': True})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def timing_auth(request):
    """
    Implementación: Timing Attack (Auth)
    """
    secret = 'password'
    return JsonResponse({'ok': secret == request.query_params.get('pwd', '')})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def user_enum_err(request):
    """
    Implementación: Username Enumeration (Error)
    """
    return JsonResponse({'error': 'User exists but wrong pwd'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def user_enum_time(request):
    """
    Implementación: Username Enumeration (Timing)
    """
    import time
    if request.query_params.get('u') == 'admin': time.sleep(0.5)
    return JsonResponse({'ok': True})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def brute_login(request):
    """
    Implementación: Lack of Rate Limiting (Login)
    """
    return JsonResponse({'status': 'intentado sin limite'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def plain_pwd(request):
    """
    Implementación: Insecure Password Storage (Simulated)
    """
    return JsonResponse({'pwd': 'base64_encoded_simulated'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def bola_upd(request):
    """
    Implementación: BOLA (Broken Object Level Auth) - Update
    """
    return JsonResponse({'ok': 'updated any'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def bola_view(request):
    """
    Implementación: BOLA - View
    """
    return JsonResponse({'private_data': 'exposed'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def bfla_admin(request):
    """
    Implementación: BFLA (Broken Function Level Auth) - Admin
    """
    return JsonResponse({'admin': 'data'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def force_browse(request):
    """
    Implementación: Forced Browsing
    """
    return JsonResponse({'hidden': 'found'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def mass_prof(request):
    """
    Implementación: Mass Assignment (Profile)
    """
    return JsonResponse({'ok': 'mass assigned'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def priv_head(request):
    """
    Implementación: Privilege Escalation via Header
    """
    return JsonResponse({'admin': request.META.get('HTTP_X_ADMIN') == 'True'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def idor_export(request):
    """
    Implementación: IDOR on Export
    """
    return JsonResponse({'export': 'tenant_data'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def param_role(request):
    """
    Implementación: Parameter Tampering (Role)
    """
    return JsonResponse({'role_set_to': request.query_params.get('role')})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def bypass_pay(request):
    """
    Implementación: Bypass Payment (Price=0)
    """
    return JsonResponse({'price_paid': request.query_params.get('price', 0)})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def cors_cred(request):
    """
    Implementación: CORS Wildcard with Credentials
    """
    res = JsonResponse({'ok': True})
    res['Access-Control-Allow-Origin'] = '*'
    res['Access-Control-Allow-Credentials'] = 'true'
    return res

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def verb_db(request):
    """
    Implementación: Verbose Error DB
    """
    return JsonResponse({'db_error': 'SQL syntax error near...'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def ip_leak(request):
    """
    Implementación: Internal IP Leakage
    """
    return JsonResponse({'internal_ip': '10.0.0.5'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def src_leak(request):
    """
    Implementación: Source Code Disclosure
    """
    return JsonResponse({'code': 'def sensitive():'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def ver_leak(request):
    """
    Implementación: Version Disclosure (API)
    """
    import django
    return JsonResponse({'django': django.get_version()})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_leak(request):
    """
    Implementación: API Key Leakage (Response)
    """
    return JsonResponse({'aws_key': 'AKIA...'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def pii_url(request):
    """
    Implementación: PII Leakage in URL
    """
    return JsonResponse({'url_data': request.query_params.get('email')})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def gql_leak(request):
    """
    Implementación: Graphql Introspection
    """
    return JsonResponse({'schema': '...'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def docs_exp(request):
    """
    Implementación: Swagger Exposed
    """
    return JsonResponse({'status': 'Swagger active'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def git_leak(request):
    """
    Implementación: Git Directory Exposure
    """
    return JsonResponse({'git': 'refs/heads/master'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def env_leak(request):
    """
    Implementación: Environment Variables Leak
    """
    return JsonResponse({'env_vars': 'simulated'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def ssrf_blind2(request):
    """
    Implementación: Blind SSRF
    """
    import requests
    try: requests.get(request.query_params.get('url', 'http://127.0.0.1'))
    except: pass
    return JsonResponse({'ok': True})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def ssrf_cloud(request):
    """
    Implementación: SSRF Cloud Metadata
    """
    return JsonResponse({'cloud_data': 'simulated'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def zip_slip(request):
    """
    Implementación: Zip Slip (Path Traversal in Extract)
    """
    return JsonResponse({'ok': 'Zip Slip possible'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def redos2(request):
    """
    Implementación: ReDoS (Regex Denial of Service)
    """
    import re
    # re.match(r'^(a+)+$', request.query_params.get('text', 'a'))
    return JsonResponse({'ok': True})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def ref_redir(request):
    """
    Implementación: Unvalidated Redirect (Referer)
    """
    from django.shortcuts import redirect
    return redirect(request.META.get('HTTP_REFERER', '/'))

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def cookie_http(request):
    """
    Implementación: Insecure Cookie (No HttpOnly)
    """
    res = JsonResponse({'ok': True})
    res.set_cookie('token', '123')
    return res

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def cookie_sec(request):
    """
    Implementación: Insecure Cookie (No Secure)
    """
    res = JsonResponse({'ok': True})
    res.set_cookie('token', '123', httponly=True)
    return res

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def miss_head(request):
    """
    Implementación: Missing Security Headers
    """
    return JsonResponse({'ok': True})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def clickjack(request):
    """
    Implementación: Clickjacking (Simulated)
    """
    return HttpResponse('<html><body>Test</body></html>')

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def shadow_api2(request):
    """
    Implementación: Shadow API (v0)
    """
    return JsonResponse({'legacy_data': 'exposed'})
