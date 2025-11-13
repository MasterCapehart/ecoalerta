"""
Tests para los modelos de la aplicación
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from reportes.models import Usuario, CategoriaResiduo, Reporte, Notificacion


@pytest.mark.django_db
class TestUsuario:
    """Tests para el modelo Usuario"""
    
    def test_crear_usuario_inspector(self):
        """Test crear usuario inspector"""
        user = Usuario.objects.create_user(
            username='inspector1',
            password='test123',
            tipo='inspector',
            email='inspector@test.com'
        )
        assert user.username == 'inspector1'
        assert user.tipo == 'inspector'
        assert user.check_password('test123')
        assert user.is_active is True
    
    def test_crear_usuario_ciudadano(self):
        """Test crear usuario ciudadano"""
        user = Usuario.objects.create_user(
            username='ciudadano1',
            password='test123',
            tipo='ciudadano',
            email='ciudadano@test.com'
        )
        assert user.tipo == 'ciudadano'
    
    def test_usuario_tipo_default(self):
        """Test que el tipo por defecto es ciudadano"""
        user = Usuario.objects.create_user(
            username='test',
            password='test123'
        )
        assert user.tipo == 'ciudadano'


@pytest.mark.django_db
class TestCategoriaResiduo:
    """Tests para el modelo CategoriaResiduo"""
    
    def test_crear_categoria(self):
        """Test crear categoría"""
        categoria = CategoriaResiduo.objects.create(
            nombre='Escombros',
            descripcion='Materiales de construcción'
        )
        assert categoria.nombre == 'Escombros'
        assert str(categoria) == 'Escombros'
    
    def test_categoria_sin_descripcion(self):
        """Test crear categoría sin descripción"""
        categoria = CategoriaResiduo.objects.create(nombre='Test')
        assert categoria.descripcion == ''


@pytest.mark.django_db
class TestReporte:
    """Tests para el modelo Reporte"""
    
    def test_crear_reporte(self, categoria_residuo, ciudadano_user):
        """Test crear reporte básico"""
        reporte = Reporte.objects.create(
            categoria=categoria_residuo,
            descripcion='Test reporte',
            ubicacion_lat=-29.9533,
            ubicacion_lng=-71.3395,
            creado_por=ciudadano_user
        )
        assert reporte.codigo_seguimiento is not None
        assert len(reporte.codigo_seguimiento) == 8  # Formato: XXX-XXXX
        assert reporte.estado == 'nuevo'
        assert reporte.categoria == categoria_residuo
    
    def test_codigo_seguimiento_unico(self, categoria_residuo, ciudadano_user):
        """Test que los códigos de seguimiento son únicos"""
        reporte1 = Reporte.objects.create(
            categoria=categoria_residuo,
            ubicacion_lat=-29.9533,
            ubicacion_lng=-71.3395,
            creado_por=ciudadano_user
        )
        reporte2 = Reporte.objects.create(
            categoria=categoria_residuo,
            ubicacion_lat=-29.9533,
            ubicacion_lng=-71.3395,
            creado_por=ciudadano_user
        )
        assert reporte1.codigo_seguimiento != reporte2.codigo_seguimiento
    
    def test_reporte_ubicacion_property(self, categoria_residuo, ciudadano_user):
        """Test la propiedad ubicacion"""
        reporte = Reporte.objects.create(
            categoria=categoria_residuo,
            ubicacion_lat=-29.9533,
            ubicacion_lng=-71.3395,
            creado_por=ciudadano_user
        )
        ubicacion = reporte.ubicacion
        assert ubicacion is not None
        assert ubicacion.y == -29.9533
        assert ubicacion.x == -71.3395
    
    def test_reporte_estados(self, categoria_residuo, ciudadano_user):
        """Test cambiar estados del reporte"""
        reporte = Reporte.objects.create(
            categoria=categoria_residuo,
            ubicacion_lat=-29.9533,
            ubicacion_lng=-71.3395,
            creado_por=ciudadano_user
        )
        assert reporte.estado == 'nuevo'
        
        reporte.estado = 'proceso'
        reporte.save()
        assert reporte.estado == 'proceso'
        
        reporte.estado = 'resuelto'
        reporte.save()
        assert reporte.estado == 'resuelto'
    
    def test_reporte_ordenamiento(self, multiple_reportes):
        """Test que los reportes se ordenan por fecha de creación descendente"""
        reportes = Reporte.objects.all()
        fechas = [r.fecha_creacion for r in reportes]
        assert fechas == sorted(fechas, reverse=True)


@pytest.mark.django_db
class TestNotificacion:
    """Tests para el modelo Notificacion"""
    
    def test_crear_notificacion(self, reporte):
        """Test crear notificación"""
        notificacion = Notificacion.objects.create(
            reporte=reporte,
            titulo='Nuevo reporte',
            mensaje='Se ha creado un nuevo reporte'
        )
        assert notificacion.reporte == reporte
        assert notificacion.leido is False
        assert str(notificacion) == f'Nuevo reporte - {reporte.codigo_seguimiento}'
    
    def test_notificacion_marcar_leida(self, reporte):
        """Test marcar notificación como leída"""
        notificacion = Notificacion.objects.create(
            reporte=reporte,
            titulo='Test',
            mensaje='Test mensaje'
        )
        notificacion.leido = True
        notificacion.save()
        assert notificacion.leido is True

