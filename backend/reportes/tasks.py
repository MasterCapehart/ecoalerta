"""
Tareas asíncronas con Celery
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger('reportes')


@shared_task
def geocodificar_reporte_async(reporte_id):
    """
    Geocodifica un reporte de forma asíncrona
    """
    from .models import Reporte
    from .geocoding_service import GeocodingService
    
    try:
        reporte = Reporte.objects.get(id=reporte_id)
        
        # Si ya tiene dirección completa, no hacer nada
        if reporte.direccion_completa:
            logger.info(f"Reporte {reporte.codigo_seguimiento} ya tiene dirección completa")
            return
        
        # Intentar geocodificación inversa
        GeocodingService.update_direccion_completa(reporte)
        
        # Si se obtuvo dirección completa, también actualizar el campo direccion
        if reporte.direccion_completa and not reporte.direccion:
            reporte.direccion = reporte.direccion_completa[:255]
            reporte.save(update_fields=['direccion', 'direccion_completa'])
        
        logger.info(f"Geocodificación completada para reporte {reporte.codigo_seguimiento}")
        return {'status': 'success', 'reporte_id': reporte_id}
        
    except Reporte.DoesNotExist:
        logger.error(f"Reporte {reporte_id} no encontrado para geocodificación")
        return {'status': 'error', 'message': 'Reporte no encontrado'}
    except Exception as e:
        logger.error(f"Error en geocodificación asíncrona para reporte {reporte_id}: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def calcular_prioridades_batch_async(estado=None):
    """
    Calcula prioridades en batch de forma asíncrona
    """
    from .models import Reporte
    from .priority_service import PriorityService
    
    try:
        queryset = Reporte.objects.all()
        if estado:
            queryset = queryset.filter(estado=estado)
        
        updated = PriorityService.update_priorities_batch(queryset)
        logger.info(f"Prioridades actualizadas en batch: {updated} reportes")
        return {'status': 'success', 'updated': updated}
        
    except Exception as e:
        logger.error(f"Error al calcular prioridades en batch: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def enviar_email_notificacion_async(destinatario, asunto, mensaje_html, mensaje_texto=None):
    """
    Envía email de forma asíncrona
    """
    from .notification_service import NotificationService
    
    try:
        result = NotificationService.send_email_notification(
            destinatario, asunto, mensaje_html, mensaje_texto
        )
        return {'status': 'success' if result else 'failed', 'destinatario': destinatario}
    except Exception as e:
        logger.error(f"Error al enviar email asíncrono a {destinatario}: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def generar_reporte_pdf_async(fecha_desde, fecha_hasta, usuario_id):
    """
    Genera reporte PDF de forma asíncrona
    """
    from .models import Usuario
    from .reports_service import ReportsService
    from django.http import HttpResponse
    from io import BytesIO
    import base64
    
    try:
        usuario = Usuario.objects.get(id=usuario_id)
        
        # Convertir strings a datetime si es necesario
        if isinstance(fecha_desde, str):
            from datetime import datetime
            fecha_desde = datetime.fromisoformat(fecha_desde.replace('Z', '+00:00'))
        if isinstance(fecha_hasta, str):
            from datetime import datetime
            fecha_hasta = datetime.fromisoformat(fecha_hasta.replace('Z', '+00:00'))
        
        stats = ReportsService.get_advanced_statistics(fecha_desde, fecha_hasta)
        
        buffer = BytesIO()
        ReportsService.export_to_pdf(stats, buffer)
        buffer.seek(0)
        
        # Convertir a base64 para poder retornarlo
        pdf_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        logger.info(f"Reporte PDF generado asíncronamente para usuario {usuario.username}")
        return {
            'status': 'success',
            'pdf_base64': pdf_base64,
            'filename': f'reporte_estadistico_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        }
        
    except Exception as e:
        logger.error(f"Error al generar PDF asíncrono: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def generar_reporte_gerencial_cron():
    """
    Tarea Cron: Genera el PDF ejecutivo semanal y lo envía por correo a los administradores.
    """
    from .models import Usuario
    from .reports_service import ReportsService
    from django.core.mail import EmailMessage
    from io import BytesIO
    from datetime import timedelta
    from django.conf import settings

    try:
        ahora = timezone.now()
        fecha_desde = ahora - timedelta(days=7)
        
        # 1. Obtener Estadísticas
        stats = ReportsService.get_advanced_statistics(fecha_desde, ahora)
        
        # 2. Generar PDF en memoria
        buffer = BytesIO()
        ReportsService.export_to_pdf(stats, buffer)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # 3. Preparar Email
        admins = Usuario.objects.filter(tipo='admin', is_active=True).exclude(email='')
        destinatarios = [admin.email for admin in admins if admin.email]
        
        if not destinatarios:
            logger.warning("No hay administradores con email configurado para recibir el reporte gerencial.")
            return {'status': 'warning', 'message': 'Sin destinatarios'}

        asunto = f"📊 Reporte Gerencial EcoAlerta - {ahora.strftime('%d/%m/%Y')}"
        mensaje = f"""
        Estimado equipo directivo,

        Adjunto encontrará el Resumen Operativo de EcoAlerta correspondiente a la última semana ({fecha_desde.strftime('%d/%m/%Y')} - {ahora.strftime('%d/%m/%Y')}).

        Total de reportes ingresados: {stats['totales']['total']}
        Tasa de resolución: {stats['tasa_resolucion']:.2f}%

        Atentamente,
        Servicio Automatizado EcoAlerta
        """

        email = EmailMessage(
            subject=asunto,
            body=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios,
        )
        
        filename = f'Reporte_Gerencial_{ahora.strftime("%Y%m%d")}.pdf'
        email.attach(filename, pdf_content, 'application/pdf')
        email.send(fail_silently=False)
        
        logger.info(f"Reporte gerencial enviado exitosamente a {len(destinatarios)} administradores.")
        return {'status': 'success', 'enviados': len(destinatarios)}

    except Exception as e:
        logger.error(f"Error en tarea cron generar_reporte_gerencial: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def verificar_sla_reportes():
    """
    Verifica reportes que están cerca de exceder/excedieron su SLA.
    - Envía alerta temprana (máx una vez cada 6 horas por reporte).
    - Escala automáticamente reportes excedidos (prioridad urgente + notificación).
    """
    from datetime import timedelta
    from .models import Reporte, Usuario, Notificacion
    from .notification_service import NotificationService
    from .sla_service import SLAService
    
    try:
        ahora = timezone.now()
        reportes_en_riesgo = SLAService.obtener_reportes_en_riesgo()
        reportes_excedidos = SLAService.obtener_reportes_excedidos()
        alertas_enviadas = 0
        escalados = 0
        cooldown_alerta = timedelta(hours=6)

        for reporte in reportes_en_riesgo:
            if reporte.sla_ultima_alerta and (ahora - reporte.sla_ultima_alerta) < cooldown_alerta:
                continue

            # Notificar al inspector asignado
            if reporte.asignado_a and reporte.asignado_a.email:
                horas_restantes = (reporte.fecha_limite_resolucion - ahora).total_seconds() / 3600
                asunto = f"⚠️ Alerta SLA: Reporte {reporte.codigo_seguimiento} cerca de exceder plazo"
                mensaje = f"""
                <h2>Alerta de SLA</h2>
                <p>El reporte <strong>{reporte.codigo_seguimiento}</strong> está cerca de exceder su plazo de resolución.</p>
                <p><strong>Horas restantes:</strong> {horas_restantes:.1f} horas</p>
                <p><strong>Fecha límite:</strong> {reporte.fecha_limite_resolucion.strftime('%d/%m/%Y %H:%M')}</p>
                <p><strong>Categoría:</strong> {reporte.categoria.nombre if reporte.categoria else 'N/A'}</p>
                <p><strong>Prioridad:</strong> {reporte.prioridad}</p>
                """
                
                NotificationService.send_email_notification(
                    reporte.asignado_a.email,
                    asunto,
                    mensaje
                )
                alertas_enviadas += 1
                reporte.sla_ultima_alerta = ahora
                reporte.save(update_fields=['sla_ultima_alerta'])
                

        for reporte in reportes_excedidos:
            if reporte.sla_escalado:
                continue

            reporte.prioridad = 'urgente'
            reporte.sla_escalado = True
            reporte.sla_escalado_at = ahora
            reporte.save(update_fields=['prioridad', 'sla_escalado', 'sla_escalado_at'])
            escalados += 1

            asunto = f"🚨 Escalamiento SLA: Reporte {reporte.codigo_seguimiento}"
            mensaje = f"""
            <h2>Escalamiento Automático por SLA Excedido</h2>
            <p>El reporte <strong>{reporte.codigo_seguimiento}</strong> excedió su SLA y fue escalado automáticamente.</p>
            <p><strong>Fecha límite:</strong> {reporte.fecha_limite_resolucion.strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Prioridad actual:</strong> {reporte.prioridad}</p>
            """

            destinatarios = []
            if reporte.asignado_a and reporte.asignado_a.email:
                destinatarios.append(reporte.asignado_a.email)
            admins = Usuario.objects.filter(tipo='admin', is_active=True).exclude(email='')
            destinatarios.extend([admin.email for admin in admins if admin.email])

            for email in set(destinatarios):
                NotificationService.send_email_notification(email, asunto, mensaje)

            Notificacion.objects.create(
                reporte=reporte,
                titulo='SLA excedido y escalado',
                mensaje='El reporte fue escalado automáticamente a prioridad urgente.'
            )
        
        logger.info(
            "Verificación de SLA completada: %s alertas enviadas, %s reportes escalados",
            alertas_enviadas,
            escalados,
        )
        return {
            'status': 'success',
            'alertas_enviadas': alertas_enviadas,
            'reportes_escalados': escalados,
        }
        
    except Exception as e:
        logger.error(f"Error en verificación de SLA: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def asignar_reportes_automaticamente_async():
    """
    Asigna reportes automáticamente de forma asíncrona
    """
    from .assignment_service import AssignmentService
    
    try:
        resultado = AssignmentService.assign_reportes_automaticamente()
        logger.info(f"Asignación automática completada: {resultado['asignados']} reportes asignados")
        return resultado
    except Exception as e:
        logger.error(f"Error en asignación automática asíncrona: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def calcular_sla_automatico(reporte_id):
    """
    Calcula y asigna SLA automáticamente a un reporte según su categoría
    """
    from .models import Reporte
    from datetime import timedelta
    
    try:
        reporte = Reporte.objects.get(id=reporte_id)
        
        # Si ya tiene fecha límite, no recalcular
        if reporte.fecha_limite_resolucion:
            return {'status': 'skipped', 'message': 'SLA ya asignado'}
        
        # Definir SLAs por categoría (en horas)
        sla_por_categoria = {
            # Ejemplo: ajustar según necesidades reales
            1: 48,  # Residuos peligrosos: 48 horas
            2: 72,  # Residuos orgánicos: 72 horas
            3: 96,  # Residuos reciclables: 96 horas
            # Agregar más según categorías reales
        }
        
        # SLA por defecto: 72 horas
        horas_sla = sla_por_categoria.get(reporte.categoria_id if reporte.categoria else None, 72)
        
        # Calcular fecha límite
        fecha_limite = reporte.fecha_creacion + timedelta(hours=horas_sla)
        reporte.fecha_limite_resolucion = fecha_limite
        reporte.save(update_fields=['fecha_limite_resolucion'])
        
        logger.info(f"SLA calculado para reporte {reporte.codigo_seguimiento}: {horas_sla} horas")
        return {'status': 'success', 'horas_sla': horas_sla, 'fecha_limite': fecha_limite.isoformat()}
        
    except Reporte.DoesNotExist:
        logger.error(f"Reporte {reporte_id} no encontrado para calcular SLA")
        return {'status': 'error', 'message': 'Reporte no encontrado'}
    except Exception as e:
        logger.error(f"Error al calcular SLA para reporte {reporte_id}: {e}")
        return {'status': 'error', 'message': str(e)}
