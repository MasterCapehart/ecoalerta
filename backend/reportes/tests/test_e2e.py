"""
Tests E2E (End-to-End) usando Django Test Client
Simulan flujos completos de usuario
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
import json

from reportes.models import Reporte, CategoriaResiduo

User = get_user_model()


class E2EAuthenticationTest(TestCase):
    """Tests E2E de autenticación"""
    
    def setUp(self):
        self.client = Client()
        self.inspector = User.objects.create_user(
            username='inspector',
            password='1234',
            tipo='inspector',
            email='inspector@test.com'
        )
    
    def test_login_exitoso(self):
        """Test de login exitoso"""
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({
                'username': 'inspector',
                'password': '1234'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertIn('user', data)
    
    def test_login_fallido(self):
        """Test de login con credenciales incorrectas"""
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({
                'username': 'inspector',
                'password': 'wrong'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_refresh_token(self):
        """Test de refresh token"""
        # Primero hacer login
        login_response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({
                'username': 'inspector',
                'password': '1234'
            }),
            content_type='application/json'
        )
        login_data = json.loads(login_response.content)
        refresh_token = login_data['refresh']
        
        # Usar refresh token
        response = self.client.post(
            '/api/auth/refresh/',
            data=json.dumps({
                'refresh': refresh_token
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('access', data)


class E2EReporteFlowTest(TestCase):
    """Tests E2E del flujo completo de reportes"""
    
    def setUp(self):
        self.client = Client()
        self.inspector = User.objects.create_user(
            username='inspector',
            password='1234',
            tipo='inspector',
            email='inspector@test.com'
        )
        self.categoria = CategoriaResiduo.objects.create(
            nombre="Residuos Orgánicos",
            descripcion="Test"
        )
        
        # Login y obtener token
        login_response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({
                'username': 'inspector',
                'password': '1234'
            }),
            content_type='application/json'
        )
        login_data = json.loads(login_response.content)
        self.access_token = login_data['access']
    
    def get_authenticated_headers(self):
        """Obtiene headers con autenticación"""
        return {
            'HTTP_AUTHORIZATION': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def test_crear_reporte_publico(self):
        """Test de crear reporte sin autenticación (público)"""
        response = self.client.post(
            '/api/reportes/',
            data=json.dumps({
                'categoria': self.categoria.id,
                'descripcion': 'Basura en la calle',
                'lat': -33.4489,
                'lng': -70.6693,
                'email': 'ciudadano@test.com'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertIn('codigo_seguimiento', data)
        
        # Verificar que el reporte se creó
        reporte = Reporte.objects.get(codigo_seguimiento=data['codigo_seguimiento'])
        self.assertEqual(reporte.descripcion, 'Basura en la calle')
    
    def test_listar_reportes_autenticado(self):
        """Test de listar reportes con autenticación"""
        # Crear un reporte primero
        Reporte.objects.create(
            categoria=self.categoria,
            descripcion='Test',
            ubicacion_lat=-33.4489,
            ubicacion_lng=-70.6693,
            estado='nuevo'
        )
        
        response = self.client.get(
            '/api/reportes/',
            **self.get_authenticated_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertGreaterEqual(len(data['results']), 1)
    
    def test_actualizar_estado_reporte(self):
        """Test de actualizar estado de reporte"""
        reporte = Reporte.objects.create(
            categoria=self.categoria,
            descripcion='Test',
            ubicacion_lat=-33.4489,
            ubicacion_lng=-70.6693,
            estado='nuevo'
        )
        
        response = self.client.patch(
            f'/api/reportes/{reporte.id}/actualizar_estado/',
            data=json.dumps({
                'estado': 'proceso',
                'notas_internas': 'En proceso de revisión'
            }),
            content_type='application/json',
            **self.get_authenticated_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, 'proceso')
    
    def test_obtener_estadisticas(self):
        """Test de obtener estadísticas"""
        # Crear algunos reportes
        Reporte.objects.create(
            categoria=self.categoria,
            descripcion='Test 1',
            ubicacion_lat=-33.4489,
            ubicacion_lng=-70.6693,
            estado='nuevo'
        )
        Reporte.objects.create(
            categoria=self.categoria,
            descripcion='Test 2',
            ubicacion_lat=-33.4489,
            ubicacion_lng=-70.6693,
            estado='resuelto'
        )
        
        response = self.client.get(
            '/api/reportes/estadisticas/',
            **self.get_authenticated_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('total', data)
        self.assertIn('nuevos', data)
        self.assertIn('resueltos', data)


class E2EValidacionModeracionTest(TestCase):
    """Tests E2E de validación y moderación"""
    
    def setUp(self):
        self.client = Client()
        self.inspector = User.objects.create_user(
            username='inspector',
            password='1234',
            tipo='inspector',
            email='inspector@test.com'
        )
        self.categoria = CategoriaResiduo.objects.create(
            nombre="Test",
            descripcion="Test"
        )
        self.reporte = Reporte.objects.create(
            categoria=self.categoria,
            descripcion='Test',
            ubicacion_lat=-33.4489,
            ubicacion_lng=-70.6693,
            estado='nuevo',
            email='ciudadano@test.com'
        )
        
        # Login
        login_response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({
                'username': 'inspector',
                'password': '1234'
            }),
            content_type='application/json'
        )
        login_data = json.loads(login_response.content)
        self.access_token = login_data['access']
    
    def get_authenticated_headers(self):
        return {
            'HTTP_AUTHORIZATION': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def test_validar_reporte(self):
        """Test de validar reporte"""
        response = self.client.post(
            f'/api/reportes/{self.reporte.id}/validar/',
            data=json.dumps({
                'validado': True,
                'notas': 'Reporte válido'
            }),
            content_type='application/json',
            **self.get_authenticated_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        
        self.reporte.refresh_from_db()
        self.assertTrue(self.reporte.validado)
        self.assertEqual(self.reporte.validado_por, self.inspector)
    
    def test_moderar_comentario(self):
        """Test de moderar comentario"""
        from reportes.models import ComentarioPublico
        
        comentario = ComentarioPublico.objects.create(
            reporte=self.reporte,
            nombre='Test User',
            email='test@test.com',
            comentario='Este es un comentario de prueba',
            moderado=False
        )
        
        # Aprobar comentario
        response = self.client.post(
            f'/api/comentarios/{comentario.id}/moderar/',
            data=json.dumps({
                'accion': 'aprobar'
            }),
            content_type='application/json',
            **self.get_authenticated_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        
        comentario.refresh_from_db()
        self.assertTrue(comentario.moderado)
    
    def test_obtener_comentarios_pendientes(self):
        """Test de obtener comentarios pendientes"""
        from reportes.models import ComentarioPublico
        
        ComentarioPublico.objects.create(
            reporte=self.reporte,
            nombre='Test User',
            email='test@test.com',
            comentario='Comentario pendiente',
            moderado=False
        )
        
        response = self.client.get(
            '/api/comentarios/pendientes/',
            **self.get_authenticated_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertGreaterEqual(len(data), 1)


class E2ESLATest(TestCase):
    """Tests E2E de SLA"""
    
    def setUp(self):
        self.client = Client()
        self.inspector = User.objects.create_user(
            username='inspector',
            password='1234',
            tipo='inspector',
            email='inspector@test.com'
        )
        self.categoria = CategoriaResiduo.objects.create(
            nombre="Test",
            descripcion="Test"
        )
        
        # Login
        login_response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({
                'username': 'inspector',
                'password': '1234'
            }),
            content_type='application/json'
        )
        login_data = json.loads(login_response.content)
        self.access_token = login_data['access']
    
    def get_authenticated_headers(self):
        return {
            'HTTP_AUTHORIZATION': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def test_obtener_estadisticas_sla(self):
        """Test de obtener estadísticas de SLA"""
        response = self.client.get(
            '/api/sla/estadisticas/',
            **self.get_authenticated_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('total_con_sla', data)
        self.assertIn('en_riesgo', data)
        self.assertIn('excedidos', data)
    
    def test_calcular_sla_reporte(self):
        """Test de calcular SLA para un reporte"""
        reporte = Reporte.objects.create(
            categoria=self.categoria,
            descripcion='Test',
            ubicacion_lat=-33.4489,
            ubicacion_lng=-70.6693,
            estado='nuevo'
        )
        
        response = self.client.post(
            f'/api/reportes/{reporte.id}/calcular-sla/',
            **self.get_authenticated_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('fecha_limite', data)
        
        reporte.refresh_from_db()
        self.assertIsNotNone(reporte.fecha_limite_resolucion)
