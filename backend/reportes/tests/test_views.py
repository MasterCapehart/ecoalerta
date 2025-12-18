"""
Tests para las vistas de la API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .test_predictions import SQLITE_TEST_DB
from django.test import override_settings

from reportes.models import Reporte, CategoriaResiduo

User = get_user_model()


@override_settings(DATABASES=SQLITE_TEST_DB)
class ReporteViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.categoria = CategoriaResiduo.objects.create(nombre="Test Categoria")
        
        # Crear usuario inspector
        self.inspector = User.objects.create_user(
            username='inspector',
            password='testpass123',
            tipo='inspector'
        )
        
        # Crear reporte de prueba
        self.reporte = Reporte.objects.create(
            categoria=self.categoria,
            descripcion="Test reporte",
            ubicacion_lat=-33.45,
            ubicacion_lng=-70.66,
            estado='nuevo'
        )
    
    def test_list_reportes_sin_autenticacion(self):
        """Los reportes pueden ser listados sin autenticación"""
        response = self.client.get('/api/reportes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_crear_reporte_sin_autenticacion(self):
        """Los ciudadanos pueden crear reportes sin autenticación"""
        data = {
            'categoria': self.categoria.id,
            'descripcion': 'Nuevo reporte',
            'lat': -33.45,
            'lng': -70.66,
        }
        response = self.client.post('/api/reportes/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('codigo_seguimiento', response.data)
    
    def test_actualizar_reporte_requiere_autenticacion(self):
        """Actualizar reportes requiere autenticación"""
        data = {'estado': 'proceso'}
        response = self.client.patch(f'/api/reportes/{self.reporte.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_estadisticas_requiere_autenticacion(self):
        """Las estadísticas requieren autenticación de inspector"""
        response = self.client.get('/api/reportes/estadisticas/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_estadisticas_con_autenticacion(self):
        """Los inspectores pueden ver estadísticas"""
        self.client.force_authenticate(user=self.inspector)
        response = self.client.get('/api/reportes/estadisticas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total', response.data)


@override_settings(DATABASES=SQLITE_TEST_DB)
class LoginViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.inspector = User.objects.create_user(
            username='inspector',
            password='testpass123',
            tipo='inspector'
        )
    
    def test_login_exitoso(self):
        """Login exitoso devuelve tokens JWT"""
        data = {
            'username': 'inspector',
            'password': 'testpass123'
        }
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
    
    def test_login_credenciales_incorrectas(self):
        """Login con credenciales incorrectas devuelve error"""
        data = {
            'username': 'inspector',
            'password': 'wrongpass'
        }
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_usuario_no_inspector(self):
        """Usuarios no inspectores no pueden hacer login"""
        ciudadano = User.objects.create_user(
            username='ciudadano',
            password='testpass123',
            tipo='ciudadano'
        )
        data = {
            'username': 'ciudadano',
            'password': 'testpass123'
        }
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(DATABASES=SQLITE_TEST_DB)
class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_health_check(self):
        """Health check devuelve estado healthy"""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['database'], 'connected')

