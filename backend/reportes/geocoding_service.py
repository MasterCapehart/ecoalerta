"""
Servicio para geocodificación inversa (coordenadas -> dirección)
"""
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

logger = logging.getLogger('reportes')


class GeocodingService:
    """Servicio para geocodificación inversa"""
    
    _geocoder = None
    
    @classmethod
    def get_geocoder(cls):
        """Obtiene instancia del geocoder (singleton)"""
        if cls._geocoder is None:
            try:
                cls._geocoder = Nominatim(user_agent="ecoalerta")
            except Exception as e:
                logger.error(f"Error al inicializar geocoder: {e}")
                cls._geocoder = None
        return cls._geocoder
    
    @staticmethod
    def reverse_geocode(lat, lng, max_retries=3):
        """
        Convierte coordenadas en dirección legible
        Retorna (direccion_completa, exito)
        """
        geocoder = GeocodingService.get_geocoder()
        
        if not geocoder:
            logger.warning("Geocoder no disponible")
            return None, False
        
        for intento in range(max_retries):
            try:
                location = geocoder.reverse((lat, lng), timeout=10)
                
                if location and location.address:
                    direccion = location.address
                    logger.info(f"Geocodificación exitosa para ({lat}, {lng}): {direccion}")
                    return direccion, True
                else:
                    logger.warning(f"No se encontró dirección para ({lat}, {lng})")
                    return None, False
                    
            except GeocoderTimedOut:
                logger.warning(f"Timeout en geocodificación (intento {intento + 1}/{max_retries})")
                if intento < max_retries - 1:
                    time.sleep(1)  # Esperar antes de reintentar
                else:
                    return None, False
                    
            except GeocoderServiceError as e:
                logger.error(f"Error del servicio de geocodificación: {e}")
                return None, False
                
            except Exception as e:
                logger.error(f"Error inesperado en geocodificación: {e}")
                return None, False
        
        return None, False
    
    @staticmethod
    def update_direccion_completa(reporte):
        """
        Actualiza la dirección completa de un reporte usando geocodificación inversa
        También actualiza el campo direccion con los primeros 255 caracteres
        """
        if not reporte.ubicacion_lat or not reporte.ubicacion_lng:
            logger.warning(f"Reporte {reporte.codigo_seguimiento} no tiene coordenadas")
            return False
        
        direccion, exito = GeocodingService.reverse_geocode(
            reporte.ubicacion_lat,
            reporte.ubicacion_lng
        )
        
        if exito and direccion:
            reporte.direccion_completa = direccion
            # Actualizar también el campo direccion (máximo 255 caracteres)
            reporte.direccion = direccion[:255] if len(direccion) > 255 else direccion
            reporte.save(update_fields=['direccion', 'direccion_completa'])
            logger.info(f"Dirección actualizada para reporte {reporte.codigo_seguimiento}: {direccion[:50]}...")
            return True
        
        return False

