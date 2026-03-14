"""
Tests para los serializers
"""
from unittest.mock import Mock, patch

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from .test_predictions import SQLITE_TEST_DB
from django.test import override_settings
from rest_framework.test import APIRequestFactory

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
            ubicacion=Point(-70.66, -33.45, srid=4326),
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


@override_settings(DATABASES=SQLITE_TEST_DB)
class ReporteSerializerDuplicateBypassTests(TestCase):
    def setUp(self):
        self.categoria = CategoriaResiduo.objects.create(nombre="Test Categoria")
        self.factory = APIRequestFactory()

    def test_permitir_duplicado_true_permte_validacion(self):
        request = self.factory.post('/api/reportes/', {
            'categoria': self.categoria.id,
            'descripcion': 'Nuevo reporte',
            'lat': -33.45,
            'lng': -70.66,
            'permitir_duplicado': 'true'
        })
        serializer = ReporteSerializer(
            data={
                'categoria': self.categoria.id,
                'descripcion': 'Nuevo reporte',
            },
            context={'request': request}
        )

        fake_qs = Mock()
        fake_qs.count.return_value = 2
        with patch(
            'reportes.duplicate_service.DuplicateDetectionService.check_potential_duplicates',
            return_value=fake_qs,
        ):
            with patch(
                'reportes.duplicate_service.DuplicateDetectionService.find_ranked_duplicates',
                return_value=[{'score': 80}],
            ):
                is_valid = serializer.is_valid()

        self.assertTrue(is_valid, serializer.errors)

    def test_dup_score_alto_sin_permitir_duplicado_rechaza(self):
        request = self.factory.post('/api/reportes/', {
            'categoria': self.categoria.id,
            'descripcion': 'Nuevo reporte',
            'lat': -33.45,
            'lng': -70.66,
        })
        serializer = ReporteSerializer(
            data={
                'categoria': self.categoria.id,
                'descripcion': 'Nuevo reporte',
            },
            context={'request': request}
        )
        fake_qs = Mock()
        fake_qs.count.return_value = 2
        with patch(
            'reportes.duplicate_service.DuplicateDetectionService.check_potential_duplicates',
            return_value=fake_qs,
        ):
            with patch(
                'reportes.duplicate_service.DuplicateDetectionService.find_ranked_duplicates',
                return_value=[{'score': 90}],
            ):
                is_valid = serializer.is_valid()

        self.assertFalse(is_valid)

