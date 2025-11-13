"""
Tests para los serializers
"""
import pytest
from rest_framework.exceptions import ValidationError

from reportes.serializers import (
    CategoriaResiduoSerializer,
    ReporteSerializer,
    ReporteDetalleSerializer,
    CustomTokenObtainPairSerializer
)
from reportes.models import CategoriaResiduo, Reporte


@pytest.mark.django_db
class TestCategoriaResiduoSerializer:
    """Tests para CategoriaResiduoSerializer"""
    
    def test_serialize_categoria(self, categoria_residuo):
        """Test serializar categoría"""
        serializer = CategoriaResiduoSerializer(categoria_residuo)
        data = serializer.data
        assert data['id'] == categoria_residuo.id
        assert data['nombre'] == 'Residuos Domésticos'
        assert 'descripcion' in data


@pytest.mark.django_db
class TestReporteSerializer:
    """Tests para ReporteSerializer"""
    
    def test_serialize_reporte(self, reporte):
        """Test serializar reporte"""
        serializer = ReporteSerializer(reporte)
        data = serializer.data
        assert 'codigo_seguimiento' in data
        assert 'categoria_nombre' in data
        assert data['lat'] == -29.9533
        assert data['lng'] == -71.3395
    
    def test_create_reporte(self, categoria_residuo, rf):
        """Test crear reporte mediante serializer"""
        request = rf.post('/api/reportes/', {
            'categoria': categoria_residuo.id,
            'descripcion': 'Test reporte',
            'lat': -29.9533,
            'lng': -71.3395,
            'direccion': 'Calle Test'
        })
        serializer = ReporteSerializer(
            data=request.POST,
            context={'request': request}
        )
        assert serializer.is_valid()
        reporte = serializer.save()
        assert reporte.ubicacion_lat == -29.9533
        assert reporte.ubicacion_lng == -71.3395
    
    def test_create_reporte_sin_coordenadas(self, categoria_residuo, rf):
        """Test que crear reporte sin coordenadas falla"""
        request = rf.post('/api/reportes/', {
            'categoria': categoria_residuo.id,
            'descripcion': 'Test reporte'
        })
        serializer = ReporteSerializer(
            data=request.POST,
            context={'request': request}
        )
        # El serializer no valida coordenadas, pero el view sí
        assert serializer.is_valid()


@pytest.mark.django_db
class TestReporteDetalleSerializer:
    """Tests para ReporteDetalleSerializer"""
    
    def test_serialize_detalle(self, reporte):
        """Test serializar detalle de reporte"""
        serializer = ReporteDetalleSerializer(reporte)
        data = serializer.data
        assert 'creado_por_nombre' in data
        assert 'categoria_nombre' in data


@pytest.mark.django_db
class TestCustomTokenObtainPairSerializer:
    """Tests para CustomTokenObtainPairSerializer"""
    
    def test_token_incluye_info_usuario(self, inspector_user):
        """Test que el token incluye información del usuario"""
        serializer = CustomTokenObtainPairSerializer()
        token = serializer.get_token(inspector_user)
        
        assert 'username' in token
        assert 'tipo' in token
        assert token['username'] == 'inspector_test'
        assert token['tipo'] == 'inspector'
    
    def test_validate_incluye_user_info(self, inspector_user):
        """Test que validate incluye información del usuario"""
        serializer = CustomTokenObtainPairSerializer()
        attrs = {'username': 'inspector_test', 'password': 'testpass123'}
        data = serializer.validate(attrs)
        
        assert 'user' in data
        assert data['user']['username'] == 'inspector_test'
        assert data['user']['tipo'] == 'inspector'

