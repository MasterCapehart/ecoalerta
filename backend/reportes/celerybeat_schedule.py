"""
Configuración de tareas programadas para Celery Beat
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Verificar SLA cada hora
    'verificar-sla-reportes': {
        'task': 'reportes.tasks.verificar_sla_reportes',
        'schedule': crontab(minute=0),  # Cada hora
    },
    
    # Calcular prioridades en batch cada 6 horas
    'calcular-prioridades-batch': {
        'task': 'reportes.tasks.calcular_prioridades_batch_async',
        'schedule': crontab(minute=0, hour='*/6'),  # Cada 6 horas
    },
    
    # Asignar reportes automáticamente cada hora
    'asignar-reportes-automaticos': {
        'task': 'reportes.tasks.asignar_reportes_automaticamente_async',
        'schedule': crontab(minute=30),  # Cada hora a los 30 minutos
    },
    
    # Reporte gerencial semanal (Ejemplo: Viernes a las 18:00)
    'generar-reporte-gerencial-semanal': {
        'task': 'reportes.tasks.generar_reporte_gerencial_cron',
        'schedule': crontab(minute=0, hour=18, day_of_week='fri'),
    },
}
