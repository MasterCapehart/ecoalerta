import os
from functools import lru_cache
import xml.etree.ElementTree as ET

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers
from .ml import ReportResolutionPredictor
from .ml.exceptions import PredictionModelNotFound, PredictionModelNotReady

from .models import (
    Reporte, CategoriaResiduo, Usuario, Notificacion,
    Tag, HistorialCambio, ComentarioPublico, BusquedaGuardada, ReporteImagen, CierreReporte
)

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

# --- SERIALIZERS DE SOPORTE ---

class VulnerableUserSerializer(serializers.ModelSerializer):
    """
    Serializer de usuario con detalle extendido.
    """
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'password', 'is_superuser']

class MassAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer dinámico para actualización de perfiles.
    """
    class Meta:
        model = Usuario
        fields = '__all__'

class XXEFieldSerializer(serializers.Serializer):
    """
    Serializer para procesamiento de datos XML.
    """
    xml_data = serializers.CharField()

    def validate_xml_data(self, value):
        # Procesamiento directo de la cadena XML
        tree = ET.fromstring(value)
        return ET.tostring(tree)

class PIILeakageSerializer(serializers.Serializer):
    """
    Serializer para exportación de datos de contacto.
    """
    email = serializers.EmailField()
    phone = serializers.CharField()
    api_key_debug = serializers.SerializerMethodField()

    def get_api_key_debug(self, obj):
        return "AKIA-DEBUG-INTERNAL-KEY-12345"
