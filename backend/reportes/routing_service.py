"""
Servicio para optimización de rutas para inspectores
Implementa algoritmo del viajero (TSP) simplificado
"""
import math
import logging
from itertools import permutations

logger = logging.getLogger('reportes')


class RoutingService:
    """Servicio para calcular rutas optimizadas para inspectores"""
    
    @staticmethod
    def calculate_optimal_route(reportes, punto_inicio=None):
        """
        Calcula la ruta óptima para visitar una lista de reportes
        Usa algoritmo TSP (Traveling Salesman Problem) simplificado
        
        Parámetros:
        - reportes: QuerySet o lista de reportes
        - punto_inicio: dict con 'lat' y 'lng' del punto de inicio
        
        Retorna:
        - Lista ordenada de reportes en orden óptimo
        - Distancia total estimada en km
        - Tiempo estimado en horas
        """
        if not reportes:
            return [], 0, 0
        
        # Convertir a lista si es QuerySet
        reportes_list = list(reportes) if hasattr(reportes, '__iter__') else reportes
        
        if len(reportes_list) == 1:
            return reportes_list, 0, 0
        
        # Si hay pocos reportes, usar fuerza bruta
        if len(reportes_list) <= 8:
            return RoutingService._tsp_brute_force(reportes_list, punto_inicio)
        else:
            # Para más reportes, usar algoritmo heurístico (nearest neighbor)
            return RoutingService._tsp_nearest_neighbor(reportes_list, punto_inicio)
    
    @staticmethod
    def _tsp_brute_force(reportes, punto_inicio):
        """
        Resuelve TSP usando fuerza bruta (solo para pocos puntos)
        """
        if len(reportes) <= 1:
            return reportes, 0, 0
        
        puntos = []
        if punto_inicio:
            puntos.append({
                'lat': punto_inicio['lat'],
                'lng': punto_inicio['lng'],
                'reporte': None
            })
        
        for reporte in reportes:
            if reporte.ubicacion_lat and reporte.ubicacion_lng:
                puntos.append({
                    'lat': reporte.ubicacion_lat,
                    'lng': reporte.ubicacion_lng,
                    'reporte': reporte
                })
        
        if len(puntos) <= 1:
            return [p['reporte'] for p in puntos if p['reporte']], 0, 0
        
        # Generar todas las permutaciones posibles
        indices = list(range(1, len(puntos)))  # Excluir punto inicial
        best_distance = float('inf')
        best_route = None
        
        for perm in permutations(indices):
            distance = 0
            for i in range(len(perm)):
                if i == 0:
                    # Distancia desde punto inicial
                    distance += RoutingService._haversine_distance(
                        puntos[0]['lat'], puntos[0]['lng'],
                        puntos[perm[0]]['lat'], puntos[perm[0]]['lng']
                    )
                else:
                    # Distancia entre puntos consecutivos
                    distance += RoutingService._haversine_distance(
                        puntos[perm[i-1]]['lat'], puntos[perm[i-1]]['lng'],
                        puntos[perm[i]]['lat'], puntos[perm[i]]['lng']
                    )
            
            if distance < best_distance:
                best_distance = distance
                best_route = [puntos[0]] + [puntos[i] for i in perm]
        
        # Extraer reportes en orden
        reportes_ordenados = [p['reporte'] for p in best_route if p['reporte']]
        
        # Calcular tiempo estimado (asumiendo velocidad promedio de 30 km/h)
        tiempo_horas = best_distance / 30.0
        
        return reportes_ordenados, best_distance, tiempo_horas
    
    @staticmethod
    def _tsp_nearest_neighbor(reportes, punto_inicio):
        """
        Resuelve TSP usando algoritmo nearest neighbor (heurístico)
        """
        puntos = []
        if punto_inicio:
            puntos.append({
                'lat': punto_inicio['lat'],
                'lng': punto_inicio['lng'],
                'reporte': None,
                'visitado': False
            })
        
        for reporte in reportes:
            if reporte.ubicacion_lat and reporte.ubicacion_lng:
                puntos.append({
                    'lat': reporte.ubicacion_lat,
                    'lng': reporte.ubicacion_lng,
                    'reporte': reporte,
                    'visitado': False
                })
        
        if len(puntos) <= 1:
            return [p['reporte'] for p in puntos if p['reporte']], 0, 0
        
        # Algoritmo nearest neighbor
        ruta = [puntos[0]]  # Empezar desde punto inicial
        puntos[0]['visitado'] = True
        distancia_total = 0
        
        while len([p for p in puntos if not p['visitado']]) > 0:
            punto_actual = ruta[-1]
            mejor_punto = None
            mejor_distancia = float('inf')
            
            for punto in puntos:
                if not punto['visitado']:
                    distancia = RoutingService._haversine_distance(
                        punto_actual['lat'], punto_actual['lng'],
                        punto['lat'], punto['lng']
                    )
                    if distancia < mejor_distancia:
                        mejor_distancia = distancia
                        mejor_punto = punto
            
            if mejor_punto:
                ruta.append(mejor_punto)
                mejor_punto['visitado'] = True
                distancia_total += mejor_distancia
        
        # Calcular distancia de retorno (opcional)
        if len(ruta) > 1:
            distancia_retorno = RoutingService._haversine_distance(
                ruta[-1]['lat'], ruta[-1]['lng'],
                ruta[0]['lat'], ruta[0]['lng']
            )
            distancia_total += distancia_retorno
        
        # Extraer reportes en orden
        reportes_ordenados = [p['reporte'] for p in ruta if p['reporte']]
        
        # Calcular tiempo estimado
        tiempo_horas = distancia_total / 30.0
        
        return reportes_ordenados, distancia_total, tiempo_horas
    
    @staticmethod
    def _haversine_distance(lat1, lng1, lat2, lng2):
        """
        Calcula la distancia entre dos puntos usando fórmula de Haversine
        Retorna distancia en kilómetros
        """
        R = 6371  # Radio de la Tierra en km
        
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlng / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    @staticmethod
    def get_route_for_inspector(inspector, estado='nuevo'):
        """
        Obtiene ruta optimizada para un inspector basada en sus reportes asignados
        """
        from .models import Reporte
        
        reportes = Reporte.objects.filter(
            asignado_a=inspector,
            estado=estado
        ).exclude(
            ubicacion__isnull=True
        )
        
        # Usar ubicación actual del inspector si está disponible
        punto_inicio = None
        # Usar getattr para evitar error si los campos no existen en BD
        ubicacion_lat = getattr(inspector, 'ubicacion_actual_lat', None)
        ubicacion_lng = getattr(inspector, 'ubicacion_actual_lng', None)
        if (ubicacion_lat is not None and ubicacion_lng is not None):
            punto_inicio = {
                'lat': ubicacion_lat,
                'lng': ubicacion_lng
            }
        elif reportes.exists():
            # Fallback: usar el primer reporte como punto de inicio
            primer_reporte = reportes.first()
            punto_inicio = {
                'lat': primer_reporte.ubicacion_lat,
                'lng': primer_reporte.ubicacion_lng
            }
        
        return RoutingService.calculate_optimal_route(reportes, punto_inicio)

