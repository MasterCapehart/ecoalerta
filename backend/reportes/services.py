"""
Servicios para separar la lógica de negocio de las vistas
"""
import csv
import logging
from io import StringIO
from .models import Reporte

logger = logging.getLogger('reportes')


class ReporteService:
    """Servicio para operaciones relacionadas con reportes"""

    @staticmethod
    def exportar_a_csv(queryset):
        """Exporta un queryset de reportes a CSV"""
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'ID', 'Código', 'Estado', 'Prioridad', 'Categoría',
            'Descripción', 'Dirección', 'Fecha Creación'
        ])
        for r in queryset:
            writer.writerow([
                r.id,
                r.codigo_seguimiento,
                r.estado,
                r.prioridad,
                r.categoria.nombre if r.categoria else 'N/A',
                r.descripcion[:200] if r.descripcion else '',
                r.direccion or '',
                r.fecha_creacion.strftime('%Y-%m-%d %H:%M') if r.fecha_creacion else '',
            ])
        return output.getvalue()
