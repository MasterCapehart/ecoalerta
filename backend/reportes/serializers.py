import os
from functools import lru_cache

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from .models import Reporte, CategoriaResiduo, Usuario, Notificacion
from .ml import ReportResolutionPredictor
from .ml.exceptions import PredictionModelNotFound, PredictionModelNotReady


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


def _build_payload_from_instance(reporte: Reporte):
    if not reporte.fecha_creacion:
        dias_abierto = None
    else:
        # Redondear a días completos para que sea más consistente
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


def _compute_prediction(obj: Reporte):
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
    # foto se define como ImageField para permitir escritura, pero se sobrescribe en to_representation
    foto = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Reporte
        fields = [
            'id', 'codigo_seguimiento', 'categoria', 'categoria_nombre',
            'descripcion', 'email', 'foto', 'lat', 'lng', 'direccion',
            'estado', 'notas_internas', 'fecha_creacion', 'fecha_actualizacion',
            'asignado_a', 'prediction'
        ]
        read_only_fields = ['codigo_seguimiento', 'fecha_creacion', 'fecha_actualizacion']
    
    def to_representation(self, instance):
        """Sobrescribir para devolver la URL completa de la imagen al leer"""
        representation = super().to_representation(instance)
        
        # Convertir la ruta relativa de la foto a URL completa
        if instance.foto and hasattr(instance.foto, 'url'):
            try:
                request = self.context.get('request')
                if request:
                    foto_url = instance.foto.url
                    if not foto_url.startswith('/'):
                        foto_url = f"/{foto_url}"
                    # build_absolute_uri debería usar HTTPS si está configurado correctamente
                    absolute_url = request.build_absolute_uri(foto_url)
                    # Forzar HTTPS si la URL original es HTTPS o si estamos en producción
                    if request.is_secure() or not settings.DEBUG:
                        absolute_url = absolute_url.replace('http://', 'https://', 1)
                    representation['foto'] = absolute_url
                else:
                    # Si no hay request, construir URL manualmente
                    foto_path = instance.foto.url
                    if not foto_path.startswith('/'):
                        foto_path = f"/{foto_path}"
                    # En producción, usar HTTPS
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
    
    def create(self, validated_data):
        # Extraer lat y lng del contexto y guardar directamente en campos
        lat = self.context['request'].data.get('lat')
        lng = self.context['request'].data.get('lng')
        
        # Guardar lat y lng directamente en los campos
        if lat is not None and lng is not None:
            validated_data['ubicacion_lat'] = float(lat)
            validated_data['ubicacion_lng'] = float(lng)
        
        return super().create(validated_data)

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


class ReporteDetalleSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    prediction = serializers.SerializerMethodField()
    # foto se define como ImageField para permitir escritura, pero se sobrescribe en to_representation
    foto = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Reporte
        fields = [
            'id', 'codigo_seguimiento', 'categoria', 'categoria_nombre',
            'descripcion', 'email', 'foto', 'lat', 'lng', 'direccion',
            'estado', 'notas_internas', 'fecha_creacion', 'fecha_actualizacion',
            'creado_por_nombre', 'asignado_a', 'prediction'
        ]
    
    def to_representation(self, instance):
        """Sobrescribir para devolver la URL completa de la imagen al leer"""
        representation = super().to_representation(instance)
        
        # Convertir la ruta relativa de la foto a URL completa
        if instance.foto and hasattr(instance.foto, 'url'):
            try:
                request = self.context.get('request')
                if request:
                    foto_url = instance.foto.url
                    if not foto_url.startswith('/'):
                        foto_url = f"/{foto_url}"
                    # build_absolute_uri debería usar HTTPS si está configurado correctamente
                    absolute_url = request.build_absolute_uri(foto_url)
                    # Forzar HTTPS si la URL original es HTTPS o si estamos en producción
                    if request.is_secure() or not settings.DEBUG:
                        absolute_url = absolute_url.replace('http://', 'https://', 1)
                    representation['foto'] = absolute_url
                else:
                    # Si no hay request, construir URL manualmente
                    foto_path = instance.foto.url
                    if not foto_path.startswith('/'):
                        foto_path = f"/{foto_path}"
                    # En producción, usar HTTPS
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
