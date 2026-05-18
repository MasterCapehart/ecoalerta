"""
Servicio de búsqueda avanzada para reportes
"""
from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Concat
from django.utils import timezone
from datetime import timedelta
from django.db import connection
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import logging

logger = logging.getLogger('reportes')


class SearchService:
    """Servicio para búsqueda y filtrado avanzado de reportes"""
    
    @staticmethod
    def search_reportes(queryset, search_params):
        """
        Aplica búsqueda y filtros avanzados a un queryset de reportes
        """
        # Búsqueda full-text
        if search_params.get('q'):
            query_text = search_params['q']
            queryset = SearchService._apply_fulltext_search(queryset, query_text)
        
        # Filtros básicos
        if search_params.get('estado'):
            queryset = queryset.filter(estado=search_params['estado'])
        
        if search_params.get('categoria'):
            queryset = queryset.filter(categoria_id=search_params['categoria'])
        
        if search_params.get('asignado_a'):
            queryset = queryset.filter(asignado_a_id=search_params['asignado_a'])
        
        if search_params.get('prioridad'):
            queryset = queryset.filter(prioridad=search_params['prioridad'])
        
        if search_params.get('tags'):
            tag_ids = search_params['tags'] if isinstance(search_params['tags'], list) else [search_params['tags']]
            queryset = queryset.filter(tags__id__in=tag_ids).distinct()
        
        # Filtros de fecha
        if search_params.get('fecha_desde'):
            queryset = queryset.filter(fecha_creacion__gte=search_params['fecha_desde'])
        
        if search_params.get('fecha_hasta'):
            queryset = queryset.filter(fecha_creacion__lte=search_params['fecha_hasta'])
        
        # Búsqueda por proximidad
        if all(k in search_params for k in ['lat', 'lng', 'radio']):
            queryset = SearchService._filter_by_proximity(
                queryset,
                float(search_params['lat']),
                float(search_params['lng']),
                float(search_params['radio'])
            )
        
        # Filtros de validación
        if 'es_spam' in search_params:
            queryset = queryset.filter(es_spam=search_params['es_spam'])
        
        if 'validado' in search_params:
            queryset = queryset.filter(validado=search_params['validado'])
        
        # Ordenamiento
        ordenar_por = search_params.get('ordenar_por')
        if (not ordenar_por or ordenar_por == 'fecha_creacion') and search_params.get('q'):
            ordenar_por = '-rank'
        elif not ordenar_por:
            ordenar_por = '-fecha_creacion'
        else:
            orden = search_params.get('orden', 'desc')
            if orden == 'desc' and not ordenar_por.startswith('-'):
                ordenar_por = f'-{ordenar_por}'
        
        try:
            queryset = queryset.order_by(ordenar_por)
        except Exception:
            if ordenar_por == '-rank':
                queryset = queryset.order_by('-fecha_creacion')
            else:
                pass
        
        return queryset
    
    @staticmethod
    def _apply_fulltext_search(queryset, query_text):
        """Aplica búsqueda full-text en múltiples campos usando PostgreSQL"""
        from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
        
        # Búsqueda exacta en código
        if len(query_text) >= 3:
            exact_match = queryset.filter(codigo_seguimiento__icontains=query_text)
            if exact_match.exists():
                return exact_match.annotate(rank=Value(1.0))
        
        # Búsqueda Full-Text ponderada
        vector = (
            SearchVector('descripcion', weight='A') +
            SearchVector('direccion', weight='B') +
            SearchVector('direccion_completa', weight='B') +
            SearchVector('categoria__nombre', weight='C') +
            SearchVector('email', weight='D')
        )
        query = SearchQuery(query_text)
        
        return queryset.annotate(
            rank=SearchRank(vector, query)
        ).filter(rank__gte=0.01)
    
    @staticmethod
    def _filter_by_proximity(queryset, lat, lng, radio_km):
        """
        Filtra reportes por proximidad usando la fórmula de Haversine
        """
        lat_delta = radio_km / 111.0
        lng_delta = radio_km / (111.0 * abs(__import__('math').cos(__import__('math').radians(lat))))
        
        queryset = queryset.filter(
            ubicacion_lat__gte=lat - lat_delta,
            ubicacion_lat__lte=lat + lat_delta,
            ubicacion_lng__gte=lng - lng_delta,
            ubicacion_lng__lte=lng + lng_delta
        )
        
        return queryset
    
    @staticmethod
    def calculate_distance(lat1, lng1, lat2, lng2):
        """
        Calcula la distancia entre dos puntos usando la fórmula de Haversine
        """
        import math
        R = 6371  # Radio de la Tierra en km
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c




@api_view(['GET'])
@permission_classes([AllowAny])
def vulnerable_search(request):
    """
    Búsqueda personalizada usando SQL directo.
    """
    query_text = request.query_params.get('q', '')
    logger.info(f"Ejecutando búsqueda personalizada con: {query_text}")
    
    with connection.cursor() as cursor:
        sql = f"SELECT id, codigo_seguimiento, descripcion FROM reportes_reporte WHERE descripcion LIKE '%{query_text}%'"
        cursor.execute(sql)
        rows = cursor.fetchall()
    
    results = [{'id': r[0], 'codigo': r[1], 'descripcion': r[2]} for r in rows]
    return JsonResponse({'results': results, 'sql_executed': sql})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def sqli2(request):
    """
    Búsqueda secundaria rápida.
    """
    return JsonResponse({'ok': True})
