"""
Servicio para validación y detección de spam en reportes
"""
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import logging
import re

logger = logging.getLogger('reportes')


class ValidationService:
    """Servicio para validar reportes y detectar spam"""
    
    @staticmethod
    def validate_location(lat, lng):
        """
        Valida que las coordenadas sean válidas
        Retorna (es_valido, mensaje_error)
        """
        if lat is None or lng is None:
            return False, "Coordenadas requeridas"
        
        if not (-90 <= lat <= 90):
            return False, "Latitud debe estar entre -90 y 90"
        
        if not (-180 <= lng <= 180):
            return False, "Longitud debe estar entre -180 y 180"
        
        return True, None
    
    @staticmethod
    def detect_spam(reporte):
        """
        Detecta si un reporte es potencialmente spam
        Retorna (es_spam, score_confianza, razones)
        """
        razones = []
        score_confianza = 1.0
        
        # Verificar duplicados por ubicación
        if ValidationService._is_duplicate_location(reporte):
            razones.append("Ubicación duplicada")
            score_confianza -= 0.3
        
        # Verificar duplicados por email
        if ValidationService._is_duplicate_email(reporte):
            razones.append("Email duplicado reciente")
            score_confianza -= 0.2
        
        # Verificar contenido sospechoso
        if ValidationService._has_suspicious_content(reporte):
            razones.append("Contenido sospechoso")
            score_confianza -= 0.3
        
        # Verificar si tiene foto
        if not reporte.foto:
            score_confianza -= 0.1
        
        # Verificar si tiene descripción
        if not reporte.descripcion or len(reporte.descripcion.strip()) < 10:
            score_confianza -= 0.1
        
        score_confianza = max(0.0, min(1.0, score_confianza))
        es_spam = score_confianza < 0.5
        
        return es_spam, score_confianza, razones
    
    @staticmethod
    def _is_duplicate_location(reporte):
        """
        Verifica si hay reportes duplicados en la misma ubicación
        (Implementación compatible con no-GIS/SQLite)
        """
        from .models import Reporte
        
        if not reporte.ubicacion_lat or not reporte.ubicacion_lng:
            return False
        
        # Buscar reportes en un radio de 50 metros (aprox 0.0005 grados)
        delta = 0.0005
        
        # Filtrar primero por fecha para reducir set (últimos 7 días)
        ultimos_7_dias = timezone.now() - timedelta(days=7)
        
        # Obtenemos candidatos de la BD
        candidatos = Reporte.objects.filter(
            fecha_creacion__gte=ultimos_7_dias
        ).exclude(id=reporte.id if reporte.id else None)
        
        # Filtrar espacialmente en Python para evitar errores de DB (GIS vs Non-GIS)
        count = 0
        r_lat = reporte.ubicacion_lat
        r_lng = reporte.ubicacion_lng
        
        for cand in candidatos:
            # Usar las propiedades calculadas del modelo
            c_lat = cand.ubicacion_lat
            c_lng = cand.ubicacion_lng
            
            if c_lat is not None and c_lng is not None:
                if (abs(c_lat - r_lat) <= delta and abs(c_lng - r_lng) <= delta):
                    count += 1
                    if count >= 2:
                        return True
                        
        return False
    
    @staticmethod
    def _is_duplicate_email(reporte):
        """
        Verifica si el mismo email ha creado muchos reportes recientemente
        """
        from .models import Reporte
        
        if not reporte.email:
            return False
        
        ultimas_24_horas = timezone.now() - timedelta(hours=24)
        
        reportes_mismo_email = Reporte.objects.filter(
            email=reporte.email
        ).exclude(id=reporte.id if reporte.id else None)
        
        reportes_recientes = reportes_mismo_email.filter(
            fecha_creacion__gte=ultimas_24_horas
        )
        
        # Si hay más de 5 reportes del mismo email en 24 horas, es sospechoso
        return reportes_recientes.count() >= 5
    
    @staticmethod
    def _has_suspicious_content(reporte):
        """
        Verifica si el contenido del reporte es sospechoso
        """
        if not reporte.descripcion:
            return False
        
        descripcion_lower = reporte.descripcion.lower()
        
        # Palabras sospechosas
        palabras_spam = ['spam', 'test', 'prueba', 'xxxx', 'aaaa']
        
        for palabra in palabras_spam:
            if palabra in descripcion_lower:
                return True
        
        # Verificar si la descripción es muy corta o muy repetitiva
        if len(descripcion_lower) < 5:
            return True
        
        # Verificar repetición excesiva de caracteres
        if re.search(r'(.)\1{4,}', descripcion_lower):
            return True
        
        return False
    
    @staticmethod
    def validate_and_score(reporte):
        """
        Valida un reporte y calcula su score de confianza
        Actualiza el reporte con los resultados
        """
        # Validar ubicación
        es_valido, mensaje = ValidationService.validate_location(
            reporte.ubicacion_lat,
            reporte.ubicacion_lng
        )
        
        if not es_valido:
            logger.warning(f"Reporte {reporte.codigo_seguimiento} tiene ubicación inválida: {mensaje}")
        
        # Detectar spam
        es_spam, score_confianza, razones = ValidationService.detect_spam(reporte)
        
        # Actualizar reporte
        reporte.es_spam = es_spam
        reporte.score_confianza = score_confianza
        
        if razones:
            logger.info(f"Reporte {reporte.codigo_seguimiento} marcado como spam. Razones: {', '.join(razones)}")
        
        return {
            'es_valido': es_valido,
            'es_spam': es_spam,
            'score_confianza': score_confianza,
            'razones': razones
        }

