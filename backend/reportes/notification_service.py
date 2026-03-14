"""
Servicio para enviar notificaciones por email y SMS
"""
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger('reportes')


class NotificationService:
    """Servicio para enviar notificaciones"""
    
    @staticmethod
    def send_email_notification(destinatario, asunto, mensaje_html, mensaje_texto=None):
        """
        Envía notificación por email
        """
        try:
            if not mensaje_texto:
                mensaje_texto = strip_tags(mensaje_html)
            
            send_mail(
                subject=asunto,
                message=mensaje_texto,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@ecoalerta.cl',
                recipient_list=[destinatario],
                html_message=mensaje_html,
                fail_silently=False,
            )
            
            logger.info(f"Email enviado a {destinatario}: {asunto}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email a {destinatario}: {e}")
            return False
    
    @staticmethod
    def notify_new_report(reporte):
        """
        Notifica a inspectores sobre un nuevo reporte
        """
        from .models import Usuario
        
        inspectores = Usuario.objects.filter(tipo='inspector', is_active=True)
        
        for inspector in inspectores:
            if inspector.email:
                asunto = f"Nuevo reporte: {reporte.codigo_seguimiento}"
                mensaje = f"""
                <h2>Nuevo Reporte Creado</h2>
                <p><strong>Código:</strong> {reporte.codigo_seguimiento}</p>
                <p><strong>Categoría:</strong> {reporte.categoria.nombre if reporte.categoria else 'N/A'}</p>
                <p><strong>Ubicación:</strong> {reporte.direccion or 'N/A'}</p>
                <p><strong>Descripción:</strong> {reporte.descripcion[:100]}...</p>
                """
                
                NotificationService.send_email_notification(
                    inspector.email,
                    asunto,
                    mensaje
                )
    
    @staticmethod
    def notify_status_change(reporte, estado_anterior, estado_nuevo):
        """
        Notifica cambio de estado de un reporte
        """
        if reporte.email:
            asunto = f"Actualización de reporte: {reporte.codigo_seguimiento}"
            mensaje = f"""
            <h2>Estado Actualizado</h2>
            <p>Tu reporte <strong>{reporte.codigo_seguimiento}</strong> ha cambiado de estado:</p>
            <p><strong>Estado anterior:</strong> {estado_anterior}</p>
            <p><strong>Estado nuevo:</strong> {estado_nuevo}</p>
            <p>Puedes hacer seguimiento de tu reporte usando el código: <strong>{reporte.codigo_seguimiento}</strong></p>
            """
            
            NotificationService.send_email_notification(
                reporte.email,
                asunto,
                mensaje
            )
    
    @staticmethod
    def notify_assignment(reporte, inspector):
        """
        Notifica a un inspector sobre una nueva asignación
        """
        if inspector.email:
            asunto = f"Nuevo reporte asignado: {reporte.codigo_seguimiento}"
            mensaje = f"""
            <h2>Reporte Asignado</h2>
            <p>Se te ha asignado el reporte <strong>{reporte.codigo_seguimiento}</strong></p>
            <p><strong>Categoría:</strong> {reporte.categoria.nombre if reporte.categoria else 'N/A'}</p>
            <p><strong>Ubicación:</strong> {reporte.direccion or 'N/A'}</p>
            <p><strong>Prioridad:</strong> {reporte.prioridad}</p>
            """
            
            NotificationService.send_email_notification(
                inspector.email,
                asunto,
                mensaje
            )
    
    @staticmethod
    def notify_resolution(reporte):
        """
        Notifica al ciudadano que su reporte fue resuelto
        """
        if reporte.email:
            asunto = f"Reporte resuelto: {reporte.codigo_seguimiento}"
            mensaje = f"""
            <h2>¡Reporte Resuelto!</h2>
            <p>Tu reporte <strong>{reporte.codigo_seguimiento}</strong> ha sido marcado como resuelto.</p>
            <p>Gracias por tu colaboración en mantener nuestra ciudad limpia.</p>
            """
            
            NotificationService.send_email_notification(
                reporte.email,
                asunto,
                mensaje
            )

