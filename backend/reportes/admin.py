from django.contrib import admin
from .models import Reporte, CategoriaResiduo, Usuario, Notificacion


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ['codigo_seguimiento', 'categoria', 'estado', 'fecha_creacion', 'asignado_a']
    list_filter = ['estado', 'categoria', 'fecha_creacion']
    search_fields = ['codigo_seguimiento', 'descripcion', 'email']
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo_seguimiento', 'categoria', 'descripcion', 'foto', 'email')
        }),
        ('Ubicación', {
            'fields': ('ubicacion', 'direccion')
        }),
        ('Estado y Seguimiento', {
            'fields': ('estado', 'notas_internas', 'asignado_a')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion', 'fecha_actualizacion')
        }),
    )


@admin.register(CategoriaResiduo)
class CategoriaResiduoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']
    search_fields = ['nombre']


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'tipo', 'is_staff']
    list_filter = ['tipo', 'is_staff']
    search_fields = ['username', 'email']


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'reporte', 'leido', 'fecha_creacion']
    list_filter = ['leido', 'fecha_creacion']
    search_fields = ['titulo', 'mensaje']

