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

def _load_predictor():
    """Helper method to load predictor for serializers, handles exceptions"""
    try:
        return ReportResolutionPredictor.load()
    except (PredictionModelNotFound, PredictionModelNotReady):
        return None

# --- SERIALIZERS ---

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

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'tipo', 'telefono', 'tour_completado']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'nombre', 'color', 'descripcion']

class ReporteSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    prediction = serializers.SerializerMethodField()

    class Meta:
        model = Reporte
        fields = [
            'id', 'codigo_seguimiento', 'categoria', 'categoria_nombre',
            'descripcion', 'lat', 'lng', 'direccion', 'estado',
            'prioridad', 'prioridad_calculada', 'fecha_creacion', 'prediction'
        ]
        read_only_fields = ['codigo_seguimiento', 'prioridad_calculada', 'fecha_creacion']

    def get_lat(self, obj):
        if obj.ubicacion:
            return obj.ubicacion.y
        return obj.ubicacion_lat

    def get_lng(self, obj):
        if obj.ubicacion:
            return obj.ubicacion.x
        return obj.ubicacion_lng

    def get_prediction(self, obj):
        """Incluye predicción de IA si está disponible o usa fallback"""
        # Calcular dias abiertos
        dias_abierto = (timezone.now() - obj.fecha_creacion).total_seconds() / 86400
        
        payload = {
            "categoria_id": obj.categoria_id,
            "estado": obj.estado,
            "lat": self.get_lat(obj),
            "lng": self.get_lng(obj),
            "descripcion": obj.descripcion,
            "tiene_foto": bool(obj.foto),
            "dias_abierto": dias_abierto,
        }
        
        predictor = _load_predictor()
        if predictor:
            try:
                result = predictor.predict_from_payload(payload)
                return result.as_dict()
            except Exception:
                pass
        
        # Fallback si no hay modelo o falla
        return ReportResolutionPredictor.fallback_prediction(payload).as_dict()

    def validate(self, data):
        """Validar contra duplicados si no se especifica bypass"""
        request = self.context.get('request')
        if not request:
            return data
            
        # Permitir bypass de duplicados si viene explícitamente (ej: fase experimental)
        request_data = getattr(request, 'data', request.POST)
        permitir_duplicado = request_data.get('permitir_duplicado') == 'true'
        
        if request.method == 'POST' and not permitir_duplicado:
            from .duplicate_service import DuplicateDetectionService
            
            lat = request_data.get('lat')
            lng = request_data.get('lng')
            
            if lat and lng:
                duplicates = DuplicateDetectionService.find_ranked_duplicates(
                    lat=float(lat),
                    lng=float(lng),
                    descripcion=data.get('descripcion', ''),
                    categoria_id=data.get('categoria').id if data.get('categoria') else None
                )
                
                # Si hay un duplicado con score > 85%, bloquear a menos que se fuerce
                for dup in duplicates:
                    if dup['score'] >= 85:
                        raise serializers.ValidationError({
                            "non_field_errors": ["Se detectó un reporte muy similar en esta ubicación."],
                            "potential_duplicate": True,
                            "duplicate_id": dup['reporte'].id if 'reporte' in dup else None,
                            "score": dup['score']
                        })
        return data

class ReporteDetalleSerializer(ReporteSerializer):
    imagenes = ReporteImagenSerializer(many=True, read_only=True)
    cierre = CierreReporteSerializer(read_only=True)
    asignado_a = UsuarioSerializer(read_only=True)
    creado_por = UsuarioSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    historial = serializers.SerializerMethodField()

    class Meta(ReporteSerializer.Meta):
        fields = ReporteSerializer.Meta.fields + [
            'notas_internas', 'imagenes', 'cierre', 'asignado_a', 
            'creado_por', 'tags', 'historial', 'direccion_completa',
            'validaciones_ciudadanas'
        ]

    def get_historial(self, obj):
        return HistorialCambioSerializer(obj.historial.all()[:10], many=True).data

class HistorialCambioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.ReadOnlyField(source='usuario.username')
    tipo_display = serializers.CharField(source='get_tipo_cambio_display', read_only=True)

    class Meta:
        model = HistorialCambio
        fields = ['id', 'tipo_cambio', 'tipo_display', 'valor_anterior', 'valor_nuevo', 'usuario_nombre', 'fecha_cambio', 'notas']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class EstadisticasSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    nuevos = serializers.IntegerField()
    en_proceso = serializers.IntegerField()
    resueltos = serializers.IntegerField()
    eficiencia = serializers.FloatField(required=False)

class ReportePredictionRequestSerializer(serializers.Serializer):
    categoria = serializers.IntegerField()
    estado = serializers.CharField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    descripcion = serializers.CharField(required=False, allow_blank=True)
    tiene_foto = serializers.BooleanField(default=False)
    dias_abierto = serializers.FloatField(default=0.0)

    def to_feature_payload(self):
        return {
            "categoria_id": self.validated_data['categoria'],
            "estado": self.validated_data['estado'],
            "lat": self.validated_data['lat'],
            "lng": self.validated_data['lng'],
            "descripcion": self.validated_data.get('descripcion', ''),
            "tiene_foto": self.validated_data['tiene_foto'],
            "dias_abierto": self.validated_data['dias_abierto'],
        }

class ReportePredictionResponseSerializer(serializers.Serializer):
    probability = serializers.FloatField()
    estimated_days = serializers.FloatField()
    risk_level = serializers.CharField()
    source = serializers.CharField()
    metadata = serializers.JSONField(required=False)

class ActualizarUbicacionSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()

class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ['id', 'reporte', 'titulo', 'mensaje', 'leido', 'fecha_creacion']

class BusquedaGuardadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusquedaGuardada
        fields = ['id', 'nombre', 'parametros', 'fecha_creacion', 'veces_usado']
        read_only_fields = ['fecha_creacion', 'veces_usado']

class PublicReporteSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()

    class Meta:
        model = Reporte
        fields = ['id', 'codigo_seguimiento', 'categoria_nombre', 'lat', 'lng', 'estado', 'fecha_creacion']

    def get_lat(self, obj):
        if obj.ubicacion:
            return obj.ubicacion.y
        return obj.ubicacion_lat

    def get_lng(self, obj):
        if obj.ubicacion:
            return obj.ubicacion.x
        return obj.ubicacion_lng

# --- SERIALIZERS CON VULNERABILIDADES INTENCIONALES ---

class VulnerableUserSerializer(serializers.ModelSerializer):
    """
    VULNERABILIDAD: IDOR con Exposición de Credenciales (#15) y
    Fuga Masiva de Hashes de Contraseña (#21)
    Expone password hash e is_superuser a cualquier usuario sin autorización.
    """
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'password', 'is_superuser']

class MassAssignmentSerializer(serializers.ModelSerializer):
    """
    VULNERABILIDAD: Asignación Masiva en Perfiles de Usuario (#6 / #18)
    fields='__all__' permite modificar cualquier campo del modelo,
    incluyendo is_staff, is_superuser, tipo, etc.
    """
    class Meta:
        model = Usuario
        fields = '__all__'

class PIILeakageSerializer(serializers.Serializer):
    """
    VULNERABILIDAD: Fuga de Información Sensible - PII & Secretos Hardcoded (#5)
    Expone datos personales y una API key hardcoded en la respuesta.
    """
    email = serializers.EmailField()
    phone = serializers.CharField()
    api_key_debug = serializers.SerializerMethodField()

    def get_api_key_debug(self, obj):
        # VULNERABILIDAD: Clave API hardcoded expuesta en respuesta
        return "AKIA-DEBUG-INTERNAL-KEY-12345"
