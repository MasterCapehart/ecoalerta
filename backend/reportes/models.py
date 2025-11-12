# Models - Usando modelos estándar (sin PostGIS por ahora)
# TODO: Migrar a PostGIS cuando GDAL esté instalado correctamente en Azure
from django.db import models
from django.contrib.auth.models import AbstractUser
import secrets
import string


def generate_tracking_code():
    """Genera un código de seguimiento único"""
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(3))
    code += '-'
    code += ''.join(secrets.choice(string.digits) for _ in range(4))
    return code


class Usuario(AbstractUser):
    """Modelo de usuario personalizado"""
    TIPO_CHOICES = [
        ('inspector', 'Inspector Municipal'),
        ('ciudadano', 'Ciudadano'),
        ('admin', 'Administrador'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='ciudadano')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


class CategoriaResiduo(models.Model):
    """Categorías de residuos reportados"""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = 'Categoría de Residuo'
        verbose_name_plural = 'Categorías de Residuos'


class Reporte(models.Model):
    """Reporte de vertedero por parte de ciudadanos"""
    
    ESTADO_CHOICES = [
        ('nuevo', 'Nuevo'),
        ('proceso', 'En Proceso'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
    ]
    
    codigo_seguimiento = models.CharField(
        max_length=10, 
        unique=True, 
        default=generate_tracking_code
    )
    
    # Información básica
    categoria = models.ForeignKey(
        CategoriaResiduo, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='reportes'
    )
    descripcion = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    foto = models.ImageField(
        upload_to='reportes/', 
        blank=True, 
        null=True
    )
    
    # Ubicación geográfica
    # Usar campos de latitud y longitud temporalmente (sin PostGIS)
    # TODO: Migrar a PointField cuando GDAL esté instalado correctamente
    ubicacion_lat = models.FloatField(null=True, blank=True, db_index=True)
    ubicacion_lng = models.FloatField(null=True, blank=True, db_index=True)
    direccion = models.CharField(max_length=255, blank=True)
    
    # Propiedad para compatibilidad con código que espera ubicacion como Point
    @property
    def ubicacion(self):
        if self.ubicacion_lat is not None and self.ubicacion_lng is not None:
            # Retornar un objeto que simule un Point
            class FakePoint:
                def __init__(self, lat, lng):
                    self.y = lat
                    self.x = lng
                def __bool__(self):
                    return True
            return FakePoint(self.ubicacion_lat, self.ubicacion_lng)
        return None
    
    @ubicacion.setter
    def ubicacion(self, value):
        # Permitir asignar un Point o None
        if value is None:
            self.ubicacion_lat = None
            self.ubicacion_lng = None
        elif hasattr(value, 'y') and hasattr(value, 'x'):
            self.ubicacion_lat = value.y
            self.ubicacion_lng = value.x
    
    # Estado y seguimiento
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='nuevo'
    )
    notas_internas = models.TextField(blank=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reportes_creados'
    )
    asignado_a = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reportes_asignados'
    )
    
    def __str__(self):
        return f"{self.codigo_seguimiento} - {self.categoria.nombre if self.categoria else 'Sin categoría'}"
    
    class Meta:
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['codigo_seguimiento']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_creacion']),
        ]


class Notificacion(models.Model):
    """Notificaciones para usuarios sobre sus reportes"""
    reporte = models.ForeignKey(
        Reporte, 
        on_delete=models.CASCADE, 
        related_name='notificaciones'
    )
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.titulo} - {self.reporte.codigo_seguimiento}"
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']

