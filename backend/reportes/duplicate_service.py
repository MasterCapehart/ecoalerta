from datetime import timedelta
from difflib import SequenceMatcher
import logging
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.utils import timezone
from .models import Reporte

logger = logging.getLogger('reportes')

class DuplicateDetectionService:
    WEIGHTS = {
        'distance': 55,
        'description': 25,
        'category': 10,
        'time': 10,
    }

    @staticmethod
    def check_potential_duplicates(lat, lng, radius_meters=20, exclude_id=None):
        """
        Busca reportes abiertos cercanos a las coordenadas dadas.
        Retorna una lista de posibles duplicados.
        """
        try:
            point = Point(float(lng), float(lat), srid=4326)
            
            # Buscar reportes en el radio y que NO estén cerrados
            queryset = Reporte.objects.filter(
                ubicacion__dwithin=(point, D(m=radius_meters))
            ).exclude(
                estado__in=['resuelto', 'cerrado', 'cancelado']
            )
            
            if exclude_id:
                queryset = queryset.exclude(id=exclude_id)
                
            # Anotar con distancia
            queryset = queryset.annotate(
                distance=Distance('ubicacion', point)
            ).order_by('distance')
            # Forzar una evaluación mínima para detectar incompatibilidades GIS
            list(queryset[:1])
            return queryset
        except Exception as e:
            logger.warning("Error checking duplicates con GIS, usando fallback: %s", e)
            # Fallback para entornos sin operaciones GIS completas (ej. tests con SQLite)
            return DuplicateDetectionService._fallback_duplicates(
                lat=lat,
                lng=lng,
                radius_meters=radius_meters,
                exclude_id=exclude_id,
            )

    @staticmethod
    def find_ranked_duplicates(
        lat,
        lng,
        descripcion='',
        categoria_id=None,
        radius_meters=100,
        exclude_id=None,
        limit=5,
    ):
        """
        Retorna duplicados potenciales rankeados por score (0-100).
        """
        duplicates = DuplicateDetectionService.check_potential_duplicates(
            lat=lat,
            lng=lng,
            radius_meters=radius_meters,
            exclude_id=exclude_id,
        )
        now = timezone.now()
        ranked = []

        for reporte in duplicates:
            distance_m = DuplicateDetectionService._distance_in_meters(
                reporte,
                target_lat=float(lat),
                target_lng=float(lng),
            )
            score = DuplicateDetectionService._calculate_score(
                reporte=reporte,
                distance_m=distance_m,
                descripcion=descripcion,
                categoria_id=categoria_id,
                now=now,
            )
            ranked.append({
                'reporte': reporte,
                'score': score,
                'distance_meters': round(distance_m, 2) if distance_m is not None else None,
                'nivel': DuplicateDetectionService._score_level(score),
            })

        ranked.sort(key=lambda item: item['score'], reverse=True)
        return ranked[:limit]

    @staticmethod
    def _distance_in_meters(reporte, target_lat=None, target_lng=None):
        if hasattr(reporte, 'distance') and reporte.distance is not None:
            return float(reporte.distance.m)
        if (
            target_lat is not None
            and target_lng is not None
            and reporte.ubicacion_lat is not None
            and reporte.ubicacion_lng is not None
        ):
            return (((reporte.ubicacion_lat - target_lat) ** 2 + (reporte.ubicacion_lng - target_lng) ** 2) ** 0.5) * 111000
        return None

    @staticmethod
    def _calculate_score(reporte, distance_m, descripcion, categoria_id, now):
        # Distance: 100 si es exactamente misma ubicación, 0 si llega al umbral de radio.
        radius_reference = 100.0
        if distance_m is None:
            distance_component = 0
        else:
            distance_component = max(0.0, 1.0 - (distance_m / radius_reference))

        description_component = 0.0
        if descripcion and reporte.descripcion:
            description_component = SequenceMatcher(
                None, descripcion.lower().strip(), reporte.descripcion.lower().strip()
            ).ratio()

        category_component = 1.0 if categoria_id and reporte.categoria_id == categoria_id else 0.0

        hours_since_creation = (now - reporte.fecha_creacion).total_seconds() / 3600
        # Mayor puntaje para reportes recientes, decreciendo linealmente hasta 7 días.
        time_component = max(0.0, 1.0 - (hours_since_creation / 168.0))

        score = (
            distance_component * DuplicateDetectionService.WEIGHTS['distance']
            + description_component * DuplicateDetectionService.WEIGHTS['description']
            + category_component * DuplicateDetectionService.WEIGHTS['category']
            + time_component * DuplicateDetectionService.WEIGHTS['time']
        )
        return round(max(0.0, min(100.0, score)), 2)

    @staticmethod
    def _score_level(score):
        if score >= 70:
            return 'probable'
        if score >= 45:
            return 'posible'
        return 'bajo'

    @staticmethod
    def _fallback_duplicates(lat, lng, radius_meters=20, exclude_id=None):
        try:
            target_lat = float(lat)
            target_lng = float(lng)
        except (TypeError, ValueError):
            return Reporte.objects.none()

        recent_limit = timezone.now() - timedelta(days=14)
        queryset = Reporte.objects.filter(
            fecha_creacion__gte=recent_limit
        ).exclude(estado__in=['resuelto', 'cerrado', 'cancelado'])

        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        matches = []
        for reporte in queryset:
            if reporte.ubicacion_lat is None or reporte.ubicacion_lng is None:
                continue
            # Aproximación rápida: 1 grado ~ 111km
            distance_m = (((reporte.ubicacion_lat - target_lat) ** 2 + (reporte.ubicacion_lng - target_lng) ** 2) ** 0.5) * 111000
            if distance_m <= float(radius_meters):
                matches.append(reporte.id)

        return Reporte.objects.filter(id__in=matches)
