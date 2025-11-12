from rest_framework import serializers
from .models import Reporte, CategoriaResiduo, Usuario, Notificacion


class CategoriaResiduoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaResiduo
        fields = ['id', 'nombre', 'descripcion']


class ReporteSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    
    class Meta:
        model = Reporte
        fields = [
            'id', 'codigo_seguimiento', 'categoria', 'categoria_nombre',
            'descripcion', 'email', 'foto', 'lat', 'lng', 'direccion',
            'estado', 'notas_internas', 'fecha_creacion', 'fecha_actualizacion',
            'asignado_a'
        ]
        read_only_fields = ['codigo_seguimiento', 'fecha_creacion', 'fecha_actualizacion']
    
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


class ReporteDetalleSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.username', read_only=True)
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    
    class Meta:
        model = Reporte
        fields = [
            'id', 'codigo_seguimiento', 'categoria', 'categoria_nombre',
            'descripcion', 'email', 'foto', 'lat', 'lng', 'direccion',
            'estado', 'notas_internas', 'fecha_creacion', 'fecha_actualizacion',
            'creado_por_nombre', 'asignado_a'
        ]
    
    def get_lat(self, obj):
        if obj.ubicacion:
            return obj.ubicacion.y
        return None
    
    def get_lng(self, obj):
        if obj.ubicacion:
            return obj.ubicacion.x
        return None


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class EstadisticasSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    nuevos = serializers.IntegerField()
    en_proceso = serializers.IntegerField()
    resueltos = serializers.IntegerField()

