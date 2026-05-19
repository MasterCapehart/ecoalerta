from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Reporte
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import ReporteSerializer
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Reporte)
def notificar_cambio_reporte(sender, instance, created, **kwargs):
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        # Serializamos los datos básicos para el frontend
        data = ReporteSerializer(instance).data

        if created:
            async_to_sync(channel_layer.group_send)(
                "reportes_general",
                {
                    "type": "reporte_creado",
                    "data": data
                }
            )
        else:
            async_to_sync(channel_layer.group_send)(
                "reportes_general",
                {
                    "type": "reporte_actualizado",
                    "data": data
                }
            )
    except Exception as e:
        logger.warning(f"No se pudo enviar notificacion WebSocket: {e}")


@receiver(post_delete, sender=Reporte)
def limpiar_cache_reportes(sender, instance, **kwargs):
    cache.delete('reportes_estadisticas')
