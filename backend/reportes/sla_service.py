"""
Servicio para gestión de SLA (Service Level Agreement)
"""
import logging
from django.utils import timezone
from datetime import timedelta
from .models import Reporte, CategoriaResiduo

logger = logging.getLogger('reportes')


class SLAService:
    """Servicio para gestionar SLAs de reportes"""
    
    # SLA por categoría en horas (ajustar según necesidades)
    SLA_POR_CATEGORIA = {
        # Ejemplo: ajustar según categorías reales
        # 1: 48,   # Residuos peligrosos: 48 horas
        # 2: 72,   # Residuos orgánicos: 72 horas
        # 3: 96,   # Residuos reciclables: 96 horas
    }
    
    # SLA por defecto: 72 horas
    SLA_DEFAULT_HORAS = 72
    
    # Horas antes del límite para enviar alerta
    ALERTA_HORAS_ANTES = 24
    
    @classmethod
    def calcular_sla(cls, reporte):
        """
        Calcula y asigna SLA a un reporte según su categoría
        """
        if reporte.fecha_limite_resolucion:
            # Ya tiene SLA asignado
            return reporte.fecha_limite_resolucion
        
        # Obtener horas de SLA según categoría
        horas_sla = cls.SLA_POR_CATEGORIA.get(
            reporte.categoria_id if reporte.categoria else None,
            cls.SLA_DEFAULT_HORAS
        )
        
        # Calcular fecha límite desde fecha de creación
        fecha_limite = reporte.fecha_creacion + timedelta(hours=horas_sla)
        
        reporte.fecha_limite_resolucion = fecha_limite
        reporte.save(update_fields=['fecha_limite_resolucion'])
        
        logger.info(f"SLA calculado para reporte {reporte.codigo_seguimiento}: {horas_sla} horas")
        return fecha_limite
    
    @classmethod
    def obtener_reportes_en_riesgo(cls, horas_antes=None):
        """
        Obtiene reportes que están cerca de exceder su SLA
        """
        if horas_antes is None:
            horas_antes = cls.ALERTA_HORAS_ANTES
        
        ahora = timezone.now()
        limite_alerta = ahora + timedelta(hours=horas_antes)
        
        reportes = Reporte.objects.filter(
            fecha_limite_resolucion__isnull=False,
            fecha_limite_resolucion__lte=limite_alerta,
            fecha_limite_resolucion__gte=ahora,
            estado__in=['nuevo', 'proceso']
        ).select_related('asignado_a', 'categoria', 'creado_por')
        
        return reportes
    
    @classmethod
    def obtener_reportes_excedidos(cls):
        """
        Obtiene reportes que ya excedieron su SLA
        """
        ahora = timezone.now()
        
        reportes = Reporte.objects.filter(
            fecha_limite_resolucion__isnull=False,
            fecha_limite_resolucion__lt=ahora,
            estado__in=['nuevo', 'proceso']
        ).select_related('asignado_a', 'categoria', 'creado_por')
        
        return reportes
    
    @classmethod
    def calcular_tiempo_restante(cls, reporte):
        """
        Calcula tiempo restante hasta el límite de SLA
        Retorna None si no tiene SLA o ya excedió
        """
        if not reporte.fecha_limite_resolucion:
            return None
        
        ahora = timezone.now()
        diferencia = reporte.fecha_limite_resolucion - ahora
        
        if diferencia.total_seconds() < 0:
            # Ya excedió
            return None
        
        return diferencia
    
    @classmethod
    def obtener_estadisticas_sla(cls):
        """
        Obtiene estadísticas de SLA
        """
        ahora = timezone.now()
        
        total_con_sla = Reporte.objects.filter(
            fecha_limite_resolucion__isnull=False
        ).count()
        
        en_riesgo = cls.obtener_reportes_en_riesgo().count()
        excedidos = cls.obtener_reportes_excedidos().count()
        
        cumplidos = Reporte.objects.filter(
            fecha_limite_resolucion__isnull=False,
            estado='resuelto',
            tiempo_resolucion_horas__isnull=False
        ).exclude(
            tiempo_resolucion_horas__gt=cls.SLA_DEFAULT_HORAS
        ).count()
        
        return {
            'total_con_sla': total_con_sla,
            'en_riesgo': en_riesgo,
            'excedidos': excedidos,
            'cumplidos': cumplidos,
            'tasa_cumplimiento': (cumplidos / total_con_sla * 100) if total_con_sla > 0 else 0
        }
