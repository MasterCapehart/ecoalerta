from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    Reporte, CategoriaResiduo, Usuario, Notificacion,
    Tag, HistorialCambio, ComentarioPublico, BusquedaGuardada, CierreReporte
)


@admin.register(Reporte)
class ReporteAdmin(SimpleHistoryAdmin):
    list_display = ['codigo_seguimiento', 'categoria', 'estado', 'fecha_creacion', 'asignado_a']
    list_filter = ['estado', 'categoria', 'fecha_creacion']
    search_fields = ['codigo_seguimiento', 'descripcion', 'email']
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo_seguimiento', 'categoria', 'descripcion', 'foto', 'email')
        }),
        ('Ubicación', {
            'fields': ('ubicacion_lat', 'ubicacion_lng', 'direccion')
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
class UsuarioAdmin(SimpleHistoryAdmin):
    list_display = ['username', 'email', 'tipo', 'is_staff']
    list_filter = ['tipo', 'is_staff']
    search_fields = ['username', 'email']


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'reporte', 'leido', 'fecha_creacion']
    list_filter = ['leido', 'fecha_creacion']
    search_fields = ['titulo', 'mensaje']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'color', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']


@admin.register(HistorialCambio)
class HistorialCambioAdmin(admin.ModelAdmin):
    list_display = ['reporte', 'tipo_cambio', 'usuario', 'fecha_cambio']
    list_filter = ['tipo_cambio', 'fecha_cambio']
    search_fields = ['reporte__codigo_seguimiento', 'notas']
    readonly_fields = ['fecha_cambio']


@admin.register(ComentarioPublico)
class ComentarioPublicoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'reporte', 'moderado', 'fecha_creacion']
    list_filter = ['moderado', 'fecha_creacion']
    search_fields = ['nombre', 'email', 'comentario']


@admin.register(BusquedaGuardada)
class BusquedaGuardadaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'usuario', 'veces_usado', 'fecha_ultimo_uso']
    list_filter = ['fecha_creacion', 'fecha_ultimo_uso']
    search_fields = ['nombre', 'usuario__username']


@admin.register(CierreReporte)
class CierreReporteAdmin(admin.ModelAdmin):
    list_display = ['reporte', 'cerrado_por', 'fecha_cierre']
    list_filter = ['fecha_cierre']
    search_fields = ['reporte__codigo_seguimiento', 'evidencia_texto']
