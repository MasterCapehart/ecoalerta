"""
Tests para las vistas (views)
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from reportes.models import Reporte


@pytest.mark.django_db
class TestReporteViewSet:
    """Tests para ReporteViewSet"""
    
    def test_listar_reportes_publico(self, client, multiple_reportes):
        """Test que listar reportes es público"""
        url = reverse('reportes-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5
    
    def test_crear_reporte_publico(self, client, categoria_residuo):
        """Test que crear reporte es público"""
        url = reverse('reportes-list')
        data = {
            'categoria': categoria_residuo.id,
            'descripcion': 'Nuevo reporte',
            'lat': -29.9533,
            'lng': -71.3395,
            'direccion': 'Calle Test'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'codigo_seguimiento' in response.data
    
    def test_crear_reporte_sin_coordenadas(self, client, categoria_residuo):
        """Test que crear reporte sin coordenadas falla"""
        url = reverse('reportes-list')
        data = {
            'categoria': categoria_residuo.id,
            'descripcion': 'Nuevo reporte'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_ver_detalle_reporte_publico(self, client, reporte):
        """Test que ver detalle de reporte es público"""
        url = reverse('reportes-detail', kwargs={'pk': reporte.id})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['codigo_seguimiento'] == reporte.codigo_seguimiento
    
    def test_actualizar_estado_requiere_auth(self, client, reporte):
        """Test que actualizar estado requiere autenticación"""
        url = reverse('reportes-actualizar-estado', kwargs={'pk': reporte.id})
        data = {'estado': 'proceso'}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_actualizar_estado_con_auth(self, inspector_user, reporte):
        """Test actualizar estado con autenticación"""
        client = APIClient()
        refresh = RefreshToken.for_user(inspector_user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('reportes-actualizar-estado', kwargs={'pk': reporte.id})
        data = {'estado': 'proceso', 'notas_internas': 'En proceso'}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['estado'] == 'proceso'
    
    def test_estadisticas_requiere_auth(self, client):
        """Test que ver estadísticas requiere autenticación"""
        url = reverse('reportes-estadisticas')
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_estadisticas_con_auth(self, inspector_user, multiple_reportes):
        """Test ver estadísticas con autenticación"""
        client = APIClient()
        refresh = RefreshToken.for_user(inspector_user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('reportes-estadisticas')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 5
        assert response.data['nuevos'] == 2
        assert response.data['en_proceso'] == 2
        assert response.data['resueltos'] == 1
    
    def test_filtrar_por_estado(self, client, multiple_reportes):
        """Test filtrar reportes por estado"""
        url = reverse('reportes-list')
        response = client.get(url, {'estado': 'nuevo'})
        assert response.status_code == status.HTTP_200_OK
        # Verificar que todos los reportes tienen estado 'nuevo'
        for reporte in response.data['results']:
            assert reporte['estado'] == 'nuevo'


@pytest.mark.django_db
class TestCategoriaResiduoViewSet:
    """Tests para CategoriaResiduoViewSet"""
    
    def test_listar_categorias_publico(self, client, categoria_residuo):
        """Test que listar categorías es público"""
        url = reverse('categorias-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestJWTEndpoints:
    """Tests para endpoints de JWT"""
    
    def test_obtener_token(self, client, inspector_user):
        """Test obtener token JWT"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'inspector_test',
            'password': 'testpass123'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
        assert response.data['user']['username'] == 'inspector_test'
    
    def test_obtener_token_credenciales_invalidas(self, client):
        """Test obtener token con credenciales inválidas"""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'invalid',
            'password': 'invalid'
        }
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token(self, client, inspector_user):
        """Test refrescar token"""
        # Primero obtener un token
        url = reverse('token_obtain_pair')
        data = {
            'username': 'inspector_test',
            'password': 'testpass123'
        }
        response = client.post(url, data, format='json')
        refresh_token = response.data['refresh']
        
        # Refrescar el token
        url = reverse('token_refresh')
        response = client.post(url, {'refresh': refresh_token}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
    
    def test_verify_token(self, client, inspector_user):
        """Test verificar token"""
        # Obtener token
        refresh = RefreshToken.for_user(inspector_user)
        access_token = refresh.access_token
        
        # Verificar token
        url = reverse('token_verify')
        response = client.post(url, {'token': str(access_token)}, format='json')
        assert response.status_code == status.HTTP_200_OK

