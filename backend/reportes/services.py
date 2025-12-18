"""
Servicios para separar la lógica de negocio de las vistas
"""
import csv
import logging
from io import StringIO
from django.db.models import QuerySet
from .models import Reporte

logger = logging.getLogger('reportes')


class ReporteService:
    """Servicio para operaciones relacionadas con reportes"""
    
    @staticmethod
    def crear_reporte(data, usuario=None):
        """
        Crea un nuevo reporte
        """
        reporte = Reporte.objects.create(
            categoria_id=data.get('categoria'),
            descripcion=data.get('descripcion', ''),
            email=data.get('email', ''),
            ubicacion_lat=data.get('lat'),
            ubicacion_lng=data.get('lng'),
            direccion=data.get('direccion', ''),
            creado_por=usuario if usuario and usuario.is_authenticated else None,
        )
        
        # Guardar foto si existe
        if 'foto' in data:
            reporte.foto = data['foto']
            reporte.save()
        
        logger.info(f"Reporte creado: {reporte.codigo_seguimiento}")
        return reporte
    
    @staticmethod
    def actualizar_estado(reporte_id, nuevo_estado, notas_internas=None):
        """
        Actualiza el estado de un reporte
        """
        try:
            reporte = Reporte.objects.get(id=reporte_id)
            reporte.estado = nuevo_estado
            if notas_internas is not None:
                reporte.notas_internas = notas_internas
            reporte.save()
            
            logger.info(f"Estado actualizado para reporte {reporte.codigo_seguimiento}: {nuevo_estado}")
            return reporte
        except Reporte.DoesNotExist:
            logger.error(f"Reporte {reporte_id} no encontrado")
            raise
    
    @staticmethod
    def exportar_a_csv(queryset: QuerySet) -> str:
        """
        Exporta un queryset de reportes a CSV
        Retorna el contenido CSV como string
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        writer.writerow([
            'Código de Seguimiento',
            'Categoría',
            'Descripción',
            'Email',
            'Estado',
            'Latitud',
            'Longitud',
            'Dirección',
            'Fecha de Creación',
            'Fecha de Actualización',
            'Asignado a',
        ])
        
        # Datos
        for reporte in queryset.select_related('categoria', 'asignado_a'):
            writer.writerow([
                reporte.codigo_seguimiento,
                reporte.categoria.nombre if reporte.categoria else '',
                reporte.descripcion,
                reporte.email,
                reporte.get_estado_display(),
                reporte.ubicacion_lat,
                reporte.ubicacion_lng,
                reporte.direccion,
                reporte.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if reporte.fecha_creacion else '',
                reporte.fecha_actualizacion.strftime('%Y-%m-%d %H:%M:%S') if reporte.fecha_actualizacion else '',
                reporte.asignado_a.username if reporte.asignado_a else '',
            ])
        
        return output.getvalue()

