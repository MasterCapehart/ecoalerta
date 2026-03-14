"""
Servicio para cálculo de prioridades automáticas
"""
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('reportes')


class PriorityService:
    """Servicio para calcular prioridades automáticas de reportes"""
    
    # Pesos para el cálculo de prioridad
    PESO_ANTIGUEDAD = 0.3
    PESO_UBICACION = 0.2
    PESO_CATEGORIA = 0.2
    PESO_CONFIANZA = 0.15
    PESO_URGENCIA_MANUAL = 0.15
    
    @staticmethod
    def calculate_priority_score(reporte):
        """
        Calcula el score de prioridad para un reporte (0-100)
        Score más alto = mayor prioridad
        """
        score = 0.0
        
        # Factor de antigüedad (más antiguo = mayor prioridad)
        antiguedad_score = PriorityService._calculate_antiguedad_score(reporte)
        score += antiguedad_score * PriorityService.PESO_ANTIGUEDAD
        
        # Factor de ubicación (zonas críticas tienen mayor prioridad)
        ubicacion_score = PriorityService._calculate_ubicacion_score(reporte)
        score += ubicacion_score * PriorityService.PESO_UBICACION
        
        # Factor de categoría (algunas categorías son más urgentes)
        categoria_score = PriorityService._calculate_categoria_score(reporte)
        score += categoria_score * PriorityService.PESO_CATEGORIA
        
        # Factor de confianza (reportes más confiables tienen mayor prioridad)
        confianza_score = reporte.score_confianza * 100
        score += confianza_score * PriorityService.PESO_CONFIANZA
        
        # Factor de urgencia manual
        urgencia_manual = PriorityService._get_urgencia_manual(reporte.prioridad)
        score += urgencia_manual * PriorityService.PESO_URGENCIA_MANUAL
        
        return min(100.0, max(0.0, score))
    
    @staticmethod
    def _calculate_antiguedad_score(reporte):
        """
        Calcula score basado en antigüedad del reporte
        Reportes más antiguos tienen mayor score
        """
        ahora = timezone.now()
        antiguedad = ahora - reporte.fecha_creacion
        horas_antiguedad = antiguedad.total_seconds() / 3600
        
        # Score máximo después de 48 horas
        if horas_antiguedad >= 48:
            return 100.0
        elif horas_antiguedad >= 24:
            return 75.0
        elif horas_antiguedad >= 12:
            return 50.0
        elif horas_antiguedad >= 6:
            return 25.0
        else:
            return 10.0
    
    @staticmethod
    def _calculate_ubicacion_score(reporte):
        """
        Calcula score basado en ubicación
        Por ahora retorna un score base, se puede mejorar con datos de zonas críticas
        """
        # TODO: Integrar con datos de zonas críticas o densidad de reportes
        return 50.0  # Score base
    
    @staticmethod
    def _calculate_categoria_score(reporte):
        """
        Calcula score basado en categoría
        Algunas categorías son más urgentes que otras
        """
        if not reporte.categoria:
            return 50.0
        
        # Definir prioridades por categoría (se puede hacer configurable)
        categorias_urgentes = ['Residuos peligrosos', 'Desechos médicos']
        categorias_altas = ['Residuos orgánicos', 'Residuos de construcción']
        
        nombre_categoria = reporte.categoria.nombre.lower()
        
        for cat in categorias_urgentes:
            if cat.lower() in nombre_categoria:
                return 100.0
        
        for cat in categorias_altas:
            if cat.lower() in nombre_categoria:
                return 75.0
        
        return 50.0
    
    @staticmethod
    def _get_urgencia_manual(prioridad):
        """Convierte prioridad manual a score"""
        prioridad_map = {
            'urgente': 100.0,
            'alta': 75.0,
            'normal': 50.0,
            'baja': 25.0,
        }
        return prioridad_map.get(prioridad, 50.0)
    
    @staticmethod
    def update_priorities_batch(queryset=None):
        """
        Actualiza las prioridades calculadas para un queryset de reportes
        Si no se proporciona queryset, actualiza todos los reportes activos
        """
        from .models import Reporte
        
        if queryset is None:
            queryset = Reporte.objects.filter(estado__in=['nuevo', 'proceso'])
        
        updated = 0
        for reporte in queryset:
            score = PriorityService.calculate_priority_score(reporte)
            if reporte.prioridad_calculada != score:
                reporte.prioridad_calculada = score
                reporte.save(update_fields=['prioridad_calculada'])
                updated += 1
        
        logger.info(f"Actualizadas {updated} prioridades calculadas")
        return updated

