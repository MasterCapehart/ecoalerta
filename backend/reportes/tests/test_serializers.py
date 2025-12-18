"""
Tests para los serializers
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from .test_predictions import SQLITE_TEST_DB
from django.test import override_settings

from reportes.models import Reporte, CategoriaResiduo
from reportes.serializers import ReporteSerializer, CategoriaResiduoSerializer

User = get_user_model()


@override_settings(DATABASES=SQLITE_TEST_DB)
class ReporteSerializerTests(TestCase):
    def setUp(self):
        self.categoria = CategoriaResiduo.objects.create(nombre="Test Categoria")
        self.reporte = Reporte.objects.create(
            categoria=self.categoria,
            descripcion="Test reporte",
            ubicacion_lat=-33.45,
            ubicacion_lng=-70.66,
            estado='nuevo'
        )
    
    def test_serializer_incluye_campos_esperados(self):
        """El serializer incluye todos los campos esperados"""
        serializer = ReporteSerializer(self.reporte)
        data = serializer.data
        
        self.assertIn('id', data)
        self.assertIn('codigo_seguimiento', data)
        self.assertIn('categoria', data)
        self.assertIn('categoria_nombre', data)
        self.assertIn('descripcion', data)
        self.assertIn('lat', data)
        self.assertIn('lng', data)
        self.assertIn('estado', data)
        self.assertIn('fecha_creacion', data)
    
    def test_serializer_coordenadas_correctas(self):
        """El serializer devuelve las coordenadas correctamente"""
        serializer = ReporteSerializer(self.reporte)
        data = serializer.data
        
        self.assertEqual(data['lat'], -33.45)
        self.assertEqual(data['lng'], -70.66)


@override_settings(DATABASES=SQLITE_TEST_DB)
class CategoriaResiduoSerializerTests(TestCase):
    def setUp(self):
        self.categoria = CategoriaResiduo.objects.create(
            nombre="Test Categoria",
            descripcion="Descripción de prueba"
        )
    
    def test_serializer_incluye_campos(self):
        """El serializer incluye los campos esperados"""
        serializer = CategoriaResiduoSerializer(self.categoria)
        data = serializer.data
        
        self.assertIn('id', data)
        self.assertIn('nombre', data)
        self.assertIn('descripcion', data)
        self.assertEqual(data['nombre'], 'Test Categoria')

