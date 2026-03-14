"""
Servicio para asignación inteligente de reportes a inspectores
"""
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import logging
import math

logger = logging.getLogger('reportes')


class AssignmentService:
    """Servicio para asignación automática de reportes a inspectores"""
    
    @staticmethod
    def assign_reportes_automaticamente(reportes=None, inspectores=None):
        """
        Asigna reportes automáticamente a inspectores basado en:
        - Proximidad geográfica
        - Carga de trabajo actual
        - Especialización (si aplica)
        
        Retorna dict con asignaciones realizadas
        """
        from .models import Reporte, Usuario
        
        if reportes is None:
            reportes = Reporte.objects.filter(
                estado='nuevo',
                asignado_a__isnull=True
            ).select_related('categoria')
        
        if inspectores is None:
            inspectores = Usuario.objects.filter(
                tipo='inspector',
                is_active=True
            )
        
        if not inspectores.exists():
            logger.warning("No hay inspectores disponibles para asignación")
            return {'asignados': 0, 'detalles': []}
        
        asignaciones = []
        
        for reporte in reportes:
            inspector = AssignmentService._find_best_inspector(reporte, inspectores)
            if inspector:
                reporte.asignado_a = inspector
                reporte.save(update_fields=['asignado_a'])
                asignaciones.append({
                    'reporte': reporte.codigo_seguimiento,
                    'inspector': inspector.username,
                    'score': AssignmentService._calculate_assignment_score(reporte, inspector)
                })
                logger.info(f"Reporte {reporte.codigo_seguimiento} asignado a {inspector.username}")
        
        logger.info(f"Asignados {len(asignaciones)} reportes automáticamente")
        return {'asignados': len(asignaciones), 'detalles': asignaciones}
    
    @staticmethod
    def _find_best_inspector(reporte, inspectores):
        """
        Encuentra el mejor inspector para un reporte
        Retorna el inspector con mejor score
        """
        if not inspectores.exists():
            return None
        
        best_inspector = None
        best_score = -1
        
        for inspector in inspectores:
            score = AssignmentService._calculate_assignment_score(reporte, inspector)
            if score > best_score:
                best_score = score
                best_inspector = inspector
        
        return best_inspector
    
    @staticmethod
    def _calculate_assignment_score(reporte, inspector):
        """
        Calcula un score de asignación (0-100)
        Score más alto = mejor match
        """
        score = 100.0
        
        # Factor de carga de trabajo (menos carga = mejor score)
        carga = AssignmentService._get_workload(inspector)
        score -= carga * 0.4  # Penalizar carga alta
        
        # Factor de proximidad (más cerca = mejor score)
        proximidad_score = 50.0  # Score base por defecto
        # Usar getattr para evitar error si los campos no existen en BD
        ubicacion_lat = getattr(inspector, 'ubicacion_actual_lat', None)
        ubicacion_lng = getattr(inspector, 'ubicacion_actual_lng', None)
        if (ubicacion_lat is not None and 
            ubicacion_lng is not None and
            reporte.ubicacion_lat is not None and 
            reporte.ubicacion_lng is not None):
            # Calcular distancia usando fórmula de Haversine
            distancia = AssignmentService._haversine_distance(
                ubicacion_lat,
                ubicacion_lng,
                reporte.ubicacion_lat,
                reporte.ubicacion_lng
            )
            # Score de proximidad: más cerca = mayor score (máximo 100)
            # Distancia máxima considerada: 50km
            if distancia <= 50:
                proximidad_score = 100 - (distancia / 50) * 50  # 0-50km -> 50-100 score
            else:
                proximidad_score = max(0, 50 - ((distancia - 50) / 50) * 50)  # >50km -> 0-50 score
        score += proximidad_score * 0.3
        
        # Factor de especialización (si aplica)
        # TODO: Implementar si hay especialización por categoría
        especializacion_score = 50.0
        score += especializacion_score * 0.3
        
        return max(0.0, min(100.0, score))
    
    @staticmethod
    def _get_workload(inspector):
        """
        Calcula la carga de trabajo de un inspector
        Retorna un score de 0-100 (100 = sobrecargado)
        """
        from .models import Reporte
        
        ahora = timezone.now()
        ultimos_7_dias = ahora - timedelta(days=7)
        
        # Contar reportes activos asignados
        reportes_activos = Reporte.objects.filter(
            asignado_a=inspector,
            estado__in=['nuevo', 'proceso']
        ).count()
        
        # Contar reportes resueltos en últimos 7 días (para medir productividad)
        reportes_resueltos = Reporte.objects.filter(
            asignado_a=inspector,
            estado='resuelto',
            fecha_actualizacion__gte=ultimos_7_dias
        ).count()
        
        # Calcular carga: reportes activos / capacidad estimada
        # Capacidad estimada basada en reportes resueltos recientes
        capacidad_estimada = max(10, reportes_resueltos * 2)  # Mínimo 10
        
        carga = (reportes_activos / capacidad_estimada) * 100
        
        return min(100.0, carga)
    
    @staticmethod
    def get_inspector_statistics(inspector):
        """
        Obtiene estadísticas de un inspector para el dashboard
        """
        from .models import Reporte
        
        ahora = timezone.now()
        ultimos_30_dias = ahora - timedelta(days=30)
        
        stats = {
            'reportes_activos': Reporte.objects.filter(
                asignado_a=inspector,
                estado__in=['nuevo', 'proceso']
            ).count(),
            'reportes_resueltos_mes': Reporte.objects.filter(
                asignado_a=inspector,
                estado='resuelto',
                fecha_actualizacion__gte=ultimos_30_dias
            ).count(),
            'carga_trabajo': AssignmentService._get_workload(inspector),
            'promedio_resolucion_horas': AssignmentService._get_average_resolution_time(inspector),
        }
        
        return stats
    
    @staticmethod
    def _get_average_resolution_time(inspector):
        """
        Calcula el tiempo promedio de resolución de reportes por inspector
        Retorna horas
        """
        from .models import Reporte
        
        reportes_resueltos = Reporte.objects.filter(
            asignado_a=inspector,
            estado='resuelto',
            tiempo_resolucion_horas__isnull=False
        )
        
        if not reportes_resueltos.exists():
            return None
        
        tiempos = [r.tiempo_resolucion_horas for r in reportes_resueltos if r.tiempo_resolucion_horas]
        
        if not tiempos:
            return None
        
        return sum(tiempos) / len(tiempos)
    
    @staticmethod
    def _haversine_distance(lat1, lng1, lat2, lng2):
        """
        Calcula la distancia entre dos puntos usando la fórmula de Haversine
        Retorna distancia en kilómetros
        """
        # Radio de la Tierra en kilómetros
        R = 6371.0
        
        # Convertir a radianes
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        # Diferencia
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        # Fórmula de Haversine
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distancia = R * c
        return distancia

