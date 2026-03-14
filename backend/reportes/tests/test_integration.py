"""
Tests de integración para servicios y funcionalidades
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from django.contrib.gis.geos import Point
from reportes.models import Reporte, CategoriaResiduo, ComentarioPublico
from reportes.search_service import SearchService
from reportes.priority_service import PriorityService
from reportes.assignment_service import AssignmentService
from reportes.validation_service import ValidationService
from reportes.sla_service import SLAService
from reportes.history_service import HistoryService

User = get_user_model()


class SearchServiceIntegrationTest(TestCase):
    """Tests de integración para SearchService"""
    
    def setUp(self):
        self.categoria = CategoriaResiduo.objects.create(
            nombre="Residuos Orgánicos",
            descripcion="Test"
        )
        self.reporte1 = Reporte.objects.create(
            categoria=self.categoria,
            descripcion="Basura en la calle",
            ubicacion=Point(-70.6693, -33.4489, srid=4326),
            estado='nuevo',
            prioridad='normal'
        )
        self.reporte2 = Reporte.objects.create(
            categoria=self.categoria,
            descripcion="Desechos peligrosos",
            ubicacion=Point(-70.6700, -33.4500, srid=4326),
            estado='proceso',
            prioridad='alta'
        )
    
    def test_busqueda_full_text(self):
        """Test de búsqueda full-text"""
        queryset = Reporte.objects.all()
        resultados = SearchService.search_reportes(queryset, {'q': 'basura'})
        self.assertEqual(resultados.count(), 1)
        self.assertEqual(resultados.first(), self.reporte1)
    
    def test_busqueda_por_proximidad(self):
        """Test de búsqueda por proximidad"""
        queryset = Reporte.objects.all()
        resultados = SearchService.search_reportes(queryset, {
            'lat': -33.4489,
            'lng': -70.6693,
            'radio': 5  # 5 km
        })
        self.assertGreaterEqual(resultados.count(), 1)
    
    def test_filtro_por_estado(self):
        """Test de filtro por estado"""
        queryset = Reporte.objects.all()
        resultados = SearchService.search_reportes(queryset, {'estado': 'nuevo'})
        self.assertEqual(resultados.count(), 1)
        self.assertEqual(resultados.first().estado, 'nuevo')


class PriorityServiceIntegrationTest(TestCase):
    """Tests de integración para PriorityService"""
    
    def setUp(self):
        self.categoria = CategoriaResiduo.objects.create(
            nombre="Test",
            descripcion="Test"
        )
        self.reporte = Reporte.objects.create(
            categoria=self.categoria,
            descripcion="Test",
            ubicacion=Point(-70.6693, -33.4489, srid=4326),
            estado='nuevo',
            prioridad='normal'
        )
    
    def test_calcular_prioridad_score(self):
        """Test de cálculo de prioridad"""
        score = PriorityService.calculate_priority_score(self.reporte)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_actualizar_prioridades_batch(self):
        """Test de actualización en batch"""
        updated = PriorityService.update_priorities_batch(Reporte.objects.all())
        self.assertGreaterEqual(updated, 1)
        
        self.reporte.refresh_from_db()
        self.assertIsNotNone(self.reporte.prioridad_calculada)


class ValidationServiceIntegrationTest(TestCase):
    """Tests de integración para ValidationService"""
    
    def setUp(self):
        self.categoria = CategoriaResiduo.objects.create(
            nombre="Test",
            descripcion="Test"
        )
    
    def test_validar_ubicacion_valida(self):
        """Test de validación de ubicación válida"""
        es_valido, mensaje = ValidationService.validate_location(-33.4489, -70.6693)
        self.assertTrue(es_valido)
    
    def test_validar_ubicacion_invalida(self):
        """Test de validación de ubicación inválida"""
        es_valido, mensaje = ValidationService.validate_location(200, 200)
        self.assertFalse(es_valido)
    
    def test_validar_y_score_reporte(self):
        """Test de validación y score de reporte"""
        reporte = Reporte.objects.create(
            categoria=self.categoria,
            descripcion="Test",
            ubicacion=Point(-70.6693, -33.4489, srid=4326),
            email="test@test.com"
        )
        
        ValidationService.validate_and_score(reporte)
        reporte.refresh_from_db()
        
        self.assertIsNotNone(reporte.score_confianza)
        self.assertGreaterEqual(reporte.score_confianza, 0)
        self.assertLessEqual(reporte.score_confianza, 1)


class SLAServiceIntegrationTest(TestCase):
    """Tests de integración para SLAService"""
    
    def setUp(self):
        self.categoria = CategoriaResiduo.objects.create(
            nombre="Test",
            descripcion="Test"
        )
        self.reporte = Reporte.objects.create(
            categoria=self.categoria,
            descripcion="Test",
            ubicacion=Point(-70.6693, -33.4489, srid=4326),
            estado='nuevo'
        )
    
    def test_calcular_sla(self):
        """Test de cálculo de SLA"""
        fecha_limite = SLAService.calcular_sla(self.reporte)
        self.assertIsNotNone(fecha_limite)
        self.assertGreater(fecha_limite, self.reporte.fecha_creacion)
        
        self.reporte.refresh_from_db()
        self.assertIsNotNone(self.reporte.fecha_limite_resolucion)
    
    def test_obtener_reportes_en_riesgo(self):
        """Test de obtención de reportes en riesgo"""
        # Calcular SLA primero
        SLAService.calcular_sla(self.reporte)
        
        # Modificar fecha límite para que esté en riesgo (dentro de 24 horas)
        self.reporte.fecha_limite_resolucion = timezone.now() + timedelta(hours=12)
        self.reporte.save()
        
        reportes = SLAService.obtener_reportes_en_riesgo()
        self.assertGreaterEqual(reportes.count(), 1)
    
    def test_obtener_estadisticas_sla(self):
        """Test de obtención de estadísticas de SLA"""
        SLAService.calcular_sla(self.reporte)
        stats = SLAService.obtener_estadisticas_sla()
        
        self.assertIn('total_con_sla', stats)
        self.assertIn('en_riesgo', stats)
        self.assertIn('excedidos', stats)
        self.assertIn('cumplidos', stats)
        self.assertIn('tasa_cumplimiento', stats)


class HistoryServiceIntegrationTest(TestCase):
    """Tests de integración para HistoryService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            tipo='inspector'
        )
        self.categoria = CategoriaResiduo.objects.create(
            nombre="Test",
            descripcion="Test"
        )
        self.reporte = Reporte.objects.create(
            categoria=self.categoria,
            descripcion="Test",
            ubicacion=Point(-70.6693, -33.4489, srid=4326),
            estado='nuevo'
        )
    
    def test_registrar_cambio_estado(self):
        """Test de registro de cambio de estado"""
        HistoryService.record_state_change(
            self.reporte,
            'nuevo',
            'proceso',
            self.user
        )
        
        historial = HistoryService.get_timeline(self.reporte)
        self.assertEqual(historial.count(), 1)
        self.assertEqual(historial.first().tipo_cambio, 'estado')
    
    def test_obtener_timeline(self):
        """Test de obtención de timeline"""
        HistoryService.record_state_change(
            self.reporte,
            'nuevo',
            'proceso',
            self.user
        )
        
        timeline = HistoryService.get_timeline(self.reporte)
        self.assertGreaterEqual(timeline.count(), 1)


class AssignmentServiceIntegrationTest(TestCase):
    """Tests de integración para AssignmentService"""
    
    def setUp(self):
        self.inspector1 = User.objects.create_user(
            username='inspector1',
            password='testpass',
            tipo='inspector',
            email='inspector1@test.com'
        )
        self.inspector2 = User.objects.create_user(
            username='inspector2',
            password='testpass',
            tipo='inspector',
            email='inspector2@test.com'
        )
        self.categoria = CategoriaResiduo.objects.create(
            nombre="Test",
            descripcion="Test"
        )
        self.reporte = Reporte.objects.create(
            categoria=self.categoria,
            descripcion="Test",
            ubicacion=Point(-70.6693, -33.4489, srid=4326),
            estado='nuevo'
        )
    
    def test_obtener_estadisticas_inspector(self):
        """Test de obtención de estadísticas de inspector"""
        stats = AssignmentService.get_inspector_statistics(self.inspector1)
        
        self.assertIn('total_asignados', stats)
        self.assertIn('resueltos', stats)
        self.assertIn('en_proceso', stats)
        self.assertIn('tiempo_promedio_resolucion', stats)
    
    def test_asignar_reportes_automaticamente(self):
        """Test de asignación automática"""
        resultado = AssignmentService.assign_reportes_automaticamente()
        
        self.assertIn('asignados', resultado)
        self.assertIn('total_reportes', resultado)
        self.assertIsInstance(resultado['asignados'], int)
