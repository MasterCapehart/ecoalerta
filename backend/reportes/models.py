# Models - Usando modelos estándar (sin PostGIS por ahora)
# TODO: Migrar a PostGIS cuando GDAL esté instalado correctamente en Azure
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.auth.models import AbstractUser
import secrets
import string
from simple_history.models import HistoricalRecords


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
    # Ubicación actual del inspector (para asignación y rutas)
    ubicacion_actual_lat = models.FloatField(null=True, blank=True)
    ubicacion_actual_lng = models.FloatField(null=True, blank=True)
    fecha_actualizacion_ubicacion = models.DateTimeField(null=True, blank=True)
    tour_completado = models.BooleanField(default=False)
    history = HistoricalRecords()
    
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
    # Ubicación geográfica
    ubicacion = models.PointField(srid=4326, null=True, blank=True)
    
    # Mantenemos lat/lng como propiedades calculadas para compatibilidad hacia atrás
    @property
    def ubicacion_lat(self):
        return self.ubicacion.y if self.ubicacion else None
        
    @property
    def ubicacion_lng(self):
        return self.ubicacion.x if self.ubicacion else None
    direccion = models.CharField(max_length=255, blank=True)
    
    # (Propiedades eliminadas ya que 'ubicacion' ahora es un campo real)
    
    # Estado y seguimiento
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='nuevo'
    )
    notas_internas = models.TextField(blank=True)
    
    # Priorización y gestión
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    prioridad = models.CharField(
        max_length=20,
        choices=PRIORIDAD_CHOICES,
        default='normal'
    )
    prioridad_calculada = models.FloatField(default=0.0, db_index=True)  # Score calculado automáticamente
    tags = models.ManyToManyField('Tag', blank=True, related_name='reportes')
    
    # Validación y calidad
    score_confianza = models.FloatField(default=1.0)  # Score de confianza (0-1)
    es_spam = models.BooleanField(default=False)
    validado = models.BooleanField(default=False)
    validado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reportes_validados'
    )
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    
    # Geocodificación
    direccion_completa = models.TextField(blank=True)  # Dirección completa obtenida por geocodificación inversa
    
    # SLA y tiempos
    fecha_limite_resolucion = models.DateTimeField(null=True, blank=True)
    tiempo_resolucion_horas = models.FloatField(null=True, blank=True)  # Tiempo real de resolución
    sla_ultima_alerta = models.DateTimeField(null=True, blank=True)
    sla_escalado = models.BooleanField(default=False)
    sla_escalado_at = models.DateTimeField(null=True, blank=True)
    
    # Colaboración Ciudadana
    validaciones_ciudadanas = models.IntegerField(default=0) # Cantidad de "Lo veo también"
    
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
    history = HistoricalRecords()

    
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
            models.Index(fields=['prioridad']),
            models.Index(fields=['prioridad_calculada']),
            models.Index(fields=['es_spam']),
            models.Index(fields=['validado']),
            # Índices compuestos para consultas frecuentes
            models.Index(fields=['estado', 'fecha_creacion'], name='rpt_estado_fecha_idx'),
            models.Index(fields=['categoria', 'estado'], name='rpt_cat_estado_idx'),
            # Índice espacial es automático en PointField
            # models.Index(fields=['ubicacion_lat', 'ubicacion_lng'], name='rpt_ubicacion_idx'),
            models.Index(fields=['asignado_a', 'estado'], name='rpt_asig_estado_idx'),
            models.Index(fields=['prioridad_calculada', 'estado'], name='rpt_prio_estado_idx'),
            models.Index(fields=['asignado_a', 'estado', 'prioridad_calculada'], name='rpt_asig_est_prio_idx'),
        ]



class ReporteImagen(models.Model):
    """Imágenes adicionales para un reporte"""
    reporte = models.ForeignKey(
        Reporte,
        on_delete=models.CASCADE,
        related_name='imagenes'
    )
    imagen = models.ImageField(upload_to='reportes_galeria/')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Imagen de {self.reporte.codigo_seguimiento}"

    class Meta:
        verbose_name = 'Imagen de Reporte'
        verbose_name_plural = 'Imágenes de Reporte'


class CierreReporte(models.Model):
    """Evidencia obligatoria al cierre/resolución de un reporte"""
    reporte = models.OneToOneField(
        Reporte,
        on_delete=models.CASCADE,
        related_name='cierre'
    )
    evidencia_texto = models.TextField(blank=True)
    foto_cierre = models.ImageField(upload_to='reportes_cierre/', blank=True, null=True)
    cerrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cierres_registrados'
    )
    fecha_cierre = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cierre {self.reporte.codigo_seguimiento}"

    class Meta:
        verbose_name = 'Cierre de Reporte'
        verbose_name_plural = 'Cierres de Reportes'


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


class Tag(models.Model):
    """Etiquetas para categorizar reportes de forma flexible"""
    nombre = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#3498db')  # Color en hex
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['nombre']


class HistorialCambio(models.Model):
    """Registro de todos los cambios realizados en un reporte"""
    TIPO_CAMBIO_CHOICES = [
        ('estado', 'Cambio de Estado'),
        ('asignacion', 'Asignación'),
        ('notas', 'Notas Internas'),
        ('prioridad', 'Prioridad'),
        ('tags', 'Tags'),
        ('ubicacion', 'Ubicación'),
        ('categoria', 'Categoría'),
        ('descripcion', 'Descripción'),
        ('validacion', 'Validación'),
    ]
    
    reporte = models.ForeignKey(
        Reporte,
        on_delete=models.CASCADE,
        related_name='historial'
    )
    tipo_cambio = models.CharField(max_length=20, choices=TIPO_CAMBIO_CHOICES)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_nuevo = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cambios_realizados'
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    notas = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.reporte.codigo_seguimiento} - {self.get_tipo_cambio_display()} - {self.fecha_cambio}"
    
    class Meta:
        verbose_name = 'Historial de Cambio'
        verbose_name_plural = 'Historial de Cambios'
        ordering = ['-fecha_cambio']
        indexes = [
            models.Index(fields=['reporte', '-fecha_cambio']),
            models.Index(fields=['tipo_cambio', '-fecha_cambio']),
        ]


class ComentarioPublico(models.Model):
    """Comentarios públicos que los ciudadanos pueden agregar a reportes"""
    reporte = models.ForeignKey(
        Reporte,
        on_delete=models.CASCADE,
        related_name='comentarios_publicos'
    )
    nombre = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    comentario = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    moderado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Comentario en {self.reporte.codigo_seguimiento} por {self.nombre}"
    
    class Meta:
        verbose_name = 'Comentario Público'
        verbose_name_plural = 'Comentarios Públicos'
        ordering = ['-fecha_creacion']


class BusquedaGuardada(models.Model):
    """Búsquedas guardadas por usuarios"""
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='busquedas_guardadas'
    )
    nombre = models.CharField(max_length=100)
    parametros = models.JSONField()  # Guarda los parámetros de búsqueda
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_ultimo_uso = models.DateTimeField(auto_now=True)
    veces_usado = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.nombre} - {self.usuario.username}"
    
    class Meta:
        verbose_name = 'Búsqueda Guardada'
        verbose_name_plural = 'Búsquedas Guardadas'
        ordering = ['-fecha_ultimo_uso']
