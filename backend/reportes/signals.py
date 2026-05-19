from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Reporte
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Reporte)
def notificar_cambio_reporte(sender, instance, created, **kwargs):
    # WebSocket notifications disabled - no Redis/Channels available in this environment
    # Notifications are handled client-side via polling
    pass


@receiver(post_delete, sender=Reporte)
def limpiar_cache_reportes(sender, instance, **kwargs):
    cache.delete('reportes_estadisticas')
