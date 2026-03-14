"""
Servicio para gestionar historial de cambios en reportes
"""
import logging
from django.utils import timezone

logger = logging.getLogger('reportes')


class HistoryService:
    """Servicio para registrar y gestionar historial de cambios"""
    
    @staticmethod
    def record_change(reporte, tipo_cambio, valor_anterior, valor_nuevo, usuario=None, notas=''):
        """
        Registra un cambio en el historial de un reporte
        """
        from .models import HistorialCambio
        
        try:
            historial = HistorialCambio.objects.create(
                reporte=reporte,
                tipo_cambio=tipo_cambio,
                valor_anterior=str(valor_anterior) if valor_anterior is not None else '',
                valor_nuevo=str(valor_nuevo) if valor_nuevo is not None else '',
                usuario=usuario,
                notas=notas
            )
            
            logger.info(f"Cambio registrado: {tipo_cambio} en reporte {reporte.codigo_seguimiento}")
            return historial
            
        except Exception as e:
            logger.error(f"Error al registrar cambio: {e}")
            return None
    
    @staticmethod
    def record_state_change(reporte, estado_anterior, estado_nuevo, usuario=None):
        """Registra cambio de estado"""
        return HistoryService.record_change(
            reporte,
            'estado',
            estado_anterior,
            estado_nuevo,
            usuario,
            f"Estado cambiado de {estado_anterior} a {estado_nuevo}"
        )
    
    @staticmethod
    def record_assignment(reporte, inspector_anterior, inspector_nuevo, usuario=None):
        """Registra cambio de asignación"""
        anterior = inspector_anterior.username if inspector_anterior else 'Sin asignar'
        nuevo = inspector_nuevo.username if inspector_nuevo else 'Sin asignar'
        
        return HistoryService.record_change(
            reporte,
            'asignacion',
            anterior,
            nuevo,
            usuario,
            f"Asignación cambiada de {anterior} a {nuevo}"
        )
    
    @staticmethod
    def record_priority_change(reporte, prioridad_anterior, prioridad_nuevo, usuario=None):
        """Registra cambio de prioridad"""
        return HistoryService.record_change(
            reporte,
            'prioridad',
            prioridad_anterior,
            prioridad_nuevo,
            usuario
        )
    
    @staticmethod
    def record_tags_change(reporte, tags_anterior, tags_nuevo, usuario=None):
        """Registra cambio de tags"""
        anterior = ', '.join([t.nombre for t in tags_anterior]) if tags_anterior else 'Sin tags'
        nuevo = ', '.join([t.nombre for t in tags_nuevo]) if tags_nuevo else 'Sin tags'
        
        return HistoryService.record_change(
            reporte,
            'tags',
            anterior,
            nuevo,
            usuario
        )
    
    @staticmethod
    def record_validation_change(reporte, validado, usuario=None, notas=''):
        """Registra cambio de validación"""
        estado = 'Validado' if validado else 'Rechazado'
        return HistoryService.record_change(
            reporte,
            'validacion',
            'No validado' if not validado else None,
            estado,
            usuario,
            notas if notas else f"Reporte {estado.lower()}"
        )
    
    @staticmethod
    def get_timeline(reporte):
        """
        Obtiene el timeline completo de cambios de un reporte
        """
        from .models import HistorialCambio
        
        return HistorialCambio.objects.filter(
            reporte=reporte
        ).select_related('usuario').order_by('-fecha_cambio')

