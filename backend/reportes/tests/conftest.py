"""
Configuración compartida para todos los tests
"""
import pytest
from django.contrib.auth import get_user_model
from faker import Faker

from reportes.models import CategoriaResiduo, Reporte

fake = Faker('es_ES')
User = get_user_model()


@pytest.fixture
def inspector_user(db):
    """Crear un usuario inspector para tests"""
    return User.objects.create_user(
        username='inspector_test',
        password='testpass123',
        tipo='inspector',
        email='inspector@test.com'
    )


@pytest.fixture
def ciudadano_user(db):
    """Crear un usuario ciudadano para tests"""
    return User.objects.create_user(
        username='ciudadano_test',
        password='testpass123',
        tipo='ciudadano',
        email='ciudadano@test.com'
    )


@pytest.fixture
def admin_user(db):
    """Crear un usuario admin para tests"""
    user = User.objects.create_user(
        username='admin_test',
        password='testpass123',
        tipo='admin',
        email='admin@test.com',
        is_staff=True
    )
    return user


@pytest.fixture
def categoria_residuo(db):
    """Crear una categoría de residuo para tests"""
    return CategoriaResiduo.objects.create(
        nombre='Residuos Domésticos',
        descripcion='Residuos generados en hogares'
    )


@pytest.fixture
def reporte(db, categoria_residuo, ciudadano_user):
    """Crear un reporte para tests"""
    return Reporte.objects.create(
        categoria=categoria_residuo,
        descripcion='Vertedero ilegal encontrado',
        email='test@example.com',
        ubicacion_lat=-29.9533,
        ubicacion_lng=-71.3395,
        direccion='Calle Test 123',
        estado='nuevo',
        creado_por=ciudadano_user
    )


@pytest.fixture
def multiple_reportes(db, categoria_residuo, ciudadano_user):
    """Crear múltiples reportes para tests"""
    reportes = []
    for i in range(5):
        reporte = Reporte.objects.create(
            categoria=categoria_residuo,
            descripcion=f'Reporte de prueba {i+1}',
            email=f'test{i}@example.com',
            ubicacion_lat=-29.9533 + (i * 0.01),
            ubicacion_lng=-71.3395 + (i * 0.01),
            direccion=f'Calle Test {i+1}',
            estado='nuevo' if i < 2 else 'proceso' if i < 4 else 'resuelto',
            creado_por=ciudadano_user
        )
        reportes.append(reporte)
    return reportes

