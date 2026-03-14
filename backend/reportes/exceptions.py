"""
Manejador de excepciones personalizado para la API
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('reportes')


def custom_exception_handler(exc, context):
    """
    Manejador de excepciones personalizado que proporciona respuestas JSON consistentes
    """
    # Llamar al manejador de excepciones por defecto de DRF
    response = exception_handler(exc, context)
    
    # Si hay una respuesta, personalizarla
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': 'Ha ocurrido un error',
            'details': response.data
        }
        
        # Log del error
        logger.error(
            f"Error en {context.get('view', 'unknown')}: {exc}",
            exc_info=True
        )
        
        # Personalizar mensajes según el tipo de error
        if response.status_code == 400:
            custom_response_data['message'] = 'Error de validación'
        elif response.status_code == 401:
            custom_response_data['message'] = 'No autenticado'
        elif response.status_code == 403:
            custom_response_data['message'] = 'No autorizado'
        elif response.status_code == 404:
            custom_response_data['message'] = 'Recurso no encontrado'
        elif response.status_code == 429:
            # Rate limiting
            wait_time = response.data.get('wait', None)
            if wait_time:
                custom_response_data['message'] = f'Demasiadas solicitudes. Intenta nuevamente en {wait_time} segundos.'
            else:
                custom_response_data['message'] = 'Demasiadas solicitudes. Por favor espera un momento antes de intentar nuevamente.'
            custom_response_data['retry_after'] = wait_time
        elif response.status_code == 500:
            custom_response_data['message'] = 'Error interno del servidor'
        
        response.data = custom_response_data
    
    return response

