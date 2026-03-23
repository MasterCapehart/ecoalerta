import os
from functools import lru_cache

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from .ml import ReportResolutionPredictor
from .ml.exceptions import PredictionModelNotFound, PredictionModelNotReady

from .models import (
    Reporte, CategoriaResiduo, Usuario, Notificacion,
    Tag, HistorialCambio, ComentarioPublico, BusquedaGuardada, ReporteImagen, CierreReporte
)

# ... (rest of imports)

class ReporteImagenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporteImagen
        fields = ['id', 'imagen', 'fecha_creacion']


class CierreReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CierreReporte
        fields = ['evidencia_texto', 'foto_cierre', 'cerrado_por', 'fecha_cierre']
        read_only_fields = ['cerrado_por', 'fecha_cierre']

class CategoriaResiduoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaResiduo
        fields = ['id', 'nombre', 'descripcion']

LOCAL_PREDICTIONS_ENABLED = (
    settings.DEBUG
    or os.getenv('ENABLE_LOCAL_PREDICTIONS', 'false').lower() in ('1', 'true', 'yes')
)


@lru_cache(maxsize=1)
def _load_predictor():
    return ReportResolutionPredictor.load()


def _build_payload_from_instance(reporte):
    dias_abierto = None
    if reporte.fecha_creacion:
        dias_abierto = max(
            int((timezone.now() - reporte.fecha_creacion).total_seconds() / 86400.0),
            0,
        )

    return {
        'categoria_id': reporte.categoria_id,
        'estado': reporte.estado,
        'lat': reporte.ubicacion_lat,
        'lng': reporte.ubicacion_lng,
        'descripcion': reporte.descripcion,
        'tiene_foto': bool(reporte.foto),
        'dias_abierto': float(dias_abierto) if dias_abierto is not None else None,
    }


def _compute_prediction(obj):
    if not LOCAL_PREDICTIONS_ENABLED:
        return None
    if obj.ubicacion_lat is None or obj.ubicacion_lng is None:
        return None

    payload = _build_payload_from_instance(obj)
    try:
        predictor = _load_predictor()
        result = predictor.predict_from_payload(payload)
    except (PredictionModelNotFound, PredictionModelNotReady):
        result = ReportResolutionPredictor.fallback_prediction(payload)
    except Exception:
        return None

    data = result.as_dict()
    data['probability'] = round(data['probability'], 4)
    return data

class ReporteSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    prediction = serializers.SerializerMethodField()
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all(), required=False)
    # foto se define como ImageField para permitir escritura, pero se sobrescribe en to_representation
    foto = serializers.ImageField(required=False, allow_null=True)
    imagenes = ReporteImagenSerializer(many=True, read_only=True)
    
    class Meta:
        model = Reporte
        fields = [
            'id', 'codigo_seguimiento', 'categoria', 'categoria_nombre',
            'descripcion', 'email', 'foto', 'imagenes', 'lat', 'lng', 'direccion',
            'estado', 'notas_internas', 'fecha_creacion', 'fecha_actualizacion',
            'asignado_a', 'prediction', 'prioridad', 'prioridad_calculada',
            'tags', 'score_confianza', 'es_spam', 'validado', 'direccion_completa',
            'ai_metadata'
        ]
        read_only_fields = ['codigo_seguimiento', 'fecha_creacion', 'fecha_actualizacion']
    
    def to_representation(self, instance):
        """Sobrescribir para devolver la URL completa de la imagen al leer"""
        representation = super().to_representation(instance)
        
        # Convertir la ruta relativa de la foto a URL completa (Legacy/Thumbnail)
        if instance.foto and hasattr(instance.foto, 'url'):
            try:
                request = self.context.get('request')
                foto_path = instance.foto.url
                if not foto_path.startswith('/'):
                    foto_path = f"/{foto_path}"
                
                if request:
                    absolute_url = request.build_absolute_uri(foto_path)
                    if not settings.DEBUG and 'azurewebsites.net' in absolute_url:
                        absolute_url = absolute_url.replace('http://', 'https://', 1)
                    representation['foto'] = absolute_url
                else:
                    if not settings.DEBUG:
                        base_url = 'https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net'
                    else:
                        base_url = 'http://localhost:8000'
                    representation['foto'] = f"{base_url}{foto_path}"
            except Exception as e:
                print(f"Error al obtener URL de foto en ReporteSerializer: {e}")
                representation['foto'] = None
        else:
            representation['foto'] = None
            
        return representation
    
    def get_lat(self, obj):
        # Usar ubicacion_lat directamente o ubicacion si está disponible
        if hasattr(obj, 'ubicacion_lat') and obj.ubicacion_lat is not None:
            return obj.ubicacion_lat
        elif obj.ubicacion:
            return obj.ubicacion.y
        return None
    
    def get_lng(self, obj):
        # Usar ubicacion_lng directamente o ubicacion si está disponible
        if hasattr(obj, 'ubicacion_lng') and obj.ubicacion_lng is not None:
            return obj.ubicacion_lng
        elif obj.ubicacion:
            return obj.ubicacion.x
        return None
    
    def validate(self, data):
        """
        Validación personalizada para detectar duplicados y spam
        """
        request = self.context.get('request')
        request_data = {}
        if request:
            request_data = getattr(request, 'data', None) or getattr(request, 'POST', {})
        permitir_duplicado = False
        if request_data:
            permitir_duplicado = str(
                request_data.get('permitir_duplicado', 'false')
            ).lower() in ('1', 'true', 'yes')
        
        # 1. Validar Imagen (EXIF)
        # Validate Image Metadata (EXIF)
        if 'foto' in data:
            from .utils import validate_image_metadata
            validate_image_metadata(data['foto'])
            
        # 2. Validar Duplicados (Ubicación)
        # Necesitamos simular un objeto Reporte temporal para usar el servicio
        lat = data.get('ubicacion_lat')
        lng = data.get('ubicacion_lng')
        
        # Si vienen del request context (porque son ReadOnly en serializer fields a veces)
        if request_data and (lat is None or lng is None):
            lat = request_data.get('lat')
            lng = request_data.get('lng')

        if lat and lng:
            # Convertir a float
            try:
                lat = float(lat)
                lng = float(lng)
            except (ValueError, TypeError):
                pass
            
            from .duplicate_service import DuplicateDetectionService

            categoria = data.get('categoria')
            categoria_id = categoria.id if categoria is not None else None
            duplicates_count = DuplicateDetectionService.check_potential_duplicates(
                lat=lat,
                lng=lng,
                radius_meters=100,
            ).count()
            duplicados_rankeados = DuplicateDetectionService.find_ranked_duplicates(
                lat=lat,
                lng=lng,
                descripcion=data.get('descripcion', ''),
                categoria_id=categoria_id,
                radius_meters=100,
                limit=1,
            )
            top_score = duplicados_rankeados[0]['score'] if duplicados_rankeados else 0
            if duplicates_count >= 2 and top_score >= 70 and not permitir_duplicado:
                raise serializers.ValidationError(
                    "Detectamos un posible reporte duplicado (score alto). "
                    "Si deseas continuar, confirma manualmente."
                )

        return super().validate(data)
        
    def create(self, validated_data):
        # Extraer lat y lng del contexto
        request = self.context.get('request')
        request_data = {}
        if request:
            request_data = getattr(request, 'data', None) or getattr(request, 'POST', {})
        lat = request_data.get('lat')
        lng = request_data.get('lng')
        
        # Crear Point si hay coordenadas
        if lat is not None and lng is not None:
            try:
                from django.contrib.gis.geos import Point
                validated_data['ubicacion'] = Point(float(lng), float(lat), srid=4326)
            except (ValueError, TypeError):
                pass 
        
        reporte = super().create(validated_data)
        
        # Procesar imágenes adicionales (Key 'fotos_adicionales' o 'gallery')
        if request and request.FILES:
            # Obtener lista de imágenes con clave 'fotos[]' o 'gallery'
            fotos = request.FILES.getlist('fotos_adicionales')
            
            # Si no hay fotos adicionales explícitas, tal vez queramos guardar la 'foto' principal también en la galería?
            # Por ahora, guardamos las adicionales.
            for foto in fotos:
                ReporteImagen.objects.create(reporte=reporte, imagen=foto)
                
        return reporte

    def get_prediction(self, obj):
        return _compute_prediction(obj)


class ReportePredictionRequestSerializer(serializers.Serializer):
    categoria = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaResiduo.objects.all(),
        required=False,
        allow_null=True,
    )
    estado = serializers.ChoiceField(
        choices=[choice[0] for choice in Reporte.ESTADO_CHOICES],
        required=False,
        default='nuevo',
    )
    lat = serializers.FloatField(required=False)
    lng = serializers.FloatField(required=False)
    descripcion = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    tiene_foto = serializers.BooleanField(required=False, default=False)
    dias_abierto = serializers.FloatField(required=False, min_value=0)
    fecha_creacion = serializers.DateTimeField(required=False)

    def to_feature_payload(self):
        data = self.validated_data
        categoria = data.get('categoria')
        return {
            'categoria_id': categoria.id if categoria else None,
            'estado': data.get('estado', 'nuevo'),
            'lat': data.get('lat'),
            'lng': data.get('lng'),
            'descripcion': data.get('descripcion'),
            'tiene_foto': data.get('tiene_foto', False),
            'dias_abierto': data.get('dias_abierto'),
            'fecha_creacion': data.get('fecha_creacion').isoformat()
            if data.get('fecha_creacion')
            else None,
        }


class ReportePredictionResponseSerializer(serializers.Serializer):
    probability = serializers.FloatField()
    estimated_resolution_days = serializers.IntegerField()
    risk_level = serializers.CharField()
    source = serializers.CharField()
    metadata = serializers.JSONField()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'nombre', 'color', 'descripcion', 'fecha_creacion']


class ReporteDetalleSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    prediction = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    cierre = CierreReporteSerializer(read_only=True)
    # foto se define como ImageField para permitir escritura, pero se sobrescribe en to_representation
    foto = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Reporte
        fields = [
            'id', 'codigo_seguimiento', 'categoria', 'categoria_nombre',
            'descripcion', 'email', 'foto', 'lat', 'lng', 'direccion',
            'estado', 'notas_internas', 'fecha_creacion', 'fecha_actualizacion',
            'creado_por_nombre', 'asignado_a', 'prediction', 'prioridad',
            'prioridad_calculada', 'tags', 'score_confianza', 'es_spam',
            'validado', 'direccion_completa', 'tiempo_resolucion_horas', 'cierre',
            'ai_metadata'
        ]
    
    def to_representation(self, instance):
        """Sobrescribir para devolver la URL completa de la imagen al leer"""
        representation = super().to_representation(instance)
        
        # Convertir la ruta relativa de la foto a URL completa
        if instance.foto and hasattr(instance.foto, 'url'):
            try:
                request = self.context.get('request')
                foto_path = instance.foto.url
                if not foto_path.startswith('/'):
                    foto_path = f"/{foto_path}"
                
                if request:
                    # Usar build_absolute_uri que ya debería manejar HTTPS correctamente
                    absolute_url = request.build_absolute_uri(foto_path)
                    # Forzar HTTPS en producción (Azure)
                    if not settings.DEBUG and 'azurewebsites.net' in absolute_url:
                        absolute_url = absolute_url.replace('http://', 'https://', 1)
                    representation['foto'] = absolute_url
                else:
                    # Si no hay request, construir URL manualmente
                    if not settings.DEBUG:
                        base_url = 'https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net'
                    else:
                        base_url = 'http://localhost:8000'
                    representation['foto'] = f"{base_url}{foto_path}"
            except Exception as e:
                print(f"Error al obtener URL de foto en ReporteDetalleSerializer: {e}")
                representation['foto'] = None
        else:
            representation['foto'] = None
            
        return representation
    
    def get_lat(self, obj):
        # Usar ubicacion_lat directamente o ubicacion si está disponible
        if hasattr(obj, 'ubicacion_lat') and obj.ubicacion_lat is not None:
            return obj.ubicacion_lat
        elif hasattr(obj, 'ubicacion') and obj.ubicacion:
            return obj.ubicacion.y
        return None
    
    def get_lng(self, obj):
        # Usar ubicacion_lng directamente o ubicacion si está disponible
        if hasattr(obj, 'ubicacion_lng') and obj.ubicacion_lng is not None:
            return obj.ubicacion_lng
        elif hasattr(obj, 'ubicacion') and obj.ubicacion:
            return obj.ubicacion.x
        return None

    def get_prediction(self, obj):
        return _compute_prediction(obj)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class EstadisticasSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    nuevos = serializers.IntegerField()
    en_proceso = serializers.IntegerField()
    resueltos = serializers.IntegerField()


class HistorialCambioSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    
    class Meta:
        model = HistorialCambio
        fields = [
            'id', 'tipo_cambio', 'valor_anterior', 'valor_nuevo',
            'usuario_username', 'fecha_cambio', 'notas'
        ]


class ComentarioPublicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComentarioPublico
        fields = ['id', 'nombre', 'email', 'comentario', 'fecha_creacion']
        read_only_fields = ['fecha_creacion']


class BusquedaGuardadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusquedaGuardada
        fields = ['id', 'nombre', 'parametros', 'fecha_creacion', 'fecha_ultimo_uso', 'veces_usado']
        read_only_fields = ['fecha_creacion', 'fecha_ultimo_uso', 'veces_usado']


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para usuario (información básica)"""
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'tipo', 'telefono', 'first_name', 'last_name', 'is_staff', 'is_active', 'tour_completado']
        read_only_fields = ['id']
    
    def to_representation(self, instance):
        """Agregar campos de ubicación solo si existen en el modelo"""
        data = super().to_representation(instance)
        # Agregar campos de ubicación solo si existen en la BD (después de migración)
        if hasattr(instance, 'ubicacion_actual_lat'):
            data['ubicacion_actual_lat'] = instance.ubicacion_actual_lat
            data['ubicacion_actual_lng'] = instance.ubicacion_actual_lng
            data['fecha_actualizacion_ubicacion'] = instance.fecha_actualizacion_ubicacion
        return data


class ActualizarUbicacionSerializer(serializers.Serializer):
    """Serializer para actualizar ubicación del inspector"""
    lat = serializers.FloatField(required=True)
    lng = serializers.FloatField(required=True)


class NotificacionSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones"""
    reporte_codigo = serializers.CharField(source='reporte.codigo_seguimiento', read_only=True)
    
    class Meta:
        model = Notificacion
        fields = ['id', 'reporte', 'reporte_codigo', 'titulo', 'mensaje', 
                  'leido', 'fecha_creacion']
        read_only_fields = ['fecha_creacion']


class PublicReporteSerializer(serializers.ModelSerializer):
    """Serializer simplificado y seguro para el mapa público"""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    foto = serializers.SerializerMethodField()

    class Meta:
        model = Reporte
        fields = [
            'id', 'codigo_seguimiento', 'categoria_nombre', 'lat', 'lng', 
            'fecha_creacion', 'foto', 'estado', 'validaciones_ciudadanas'
        ]
        
    def get_lat(self, obj):
        if obj.ubicacion:
            return obj.ubicacion.y
        # Fallback a campos float si existen
        return getattr(obj, 'ubicacion_lat', None)
        
    def get_lng(self, obj):
        if obj.ubicacion:
            return obj.ubicacion.x
        # Fallback a campos float si existen
        return getattr(obj, 'ubicacion_lng', None)

    def get_foto(self, instance):
        """Sobrescribir para devolver la URL completa de la imagen al leer"""
        if instance.foto and hasattr(instance.foto, 'url'):
            try:
                request = self.context.get('request')
                foto_path = instance.foto.url
                if not foto_path.startswith('/'):
                    foto_path = f"/{foto_path}"
                
                if request:
                    absolute_url = request.build_absolute_uri(foto_path)
                    if not settings.DEBUG and 'azurewebsites.net' in absolute_url:
                        absolute_url = absolute_url.replace('http://', 'https://', 1)
                    return absolute_url
                else:
                    if not settings.DEBUG:
                        base_url = 'https://ecoalerta-backend-cmfbgrb3bgd0ephd.chilecentral-01.azurewebsites.net'
                    else:
                        base_url = 'http://localhost:8000'
                    return f"{base_url}{foto_path}"
            except Exception as e:
                pass
        return None
