"""
Configuración de Celery para tareas asíncronas
"""
import os
from celery import Celery
from django.conf import settings

# Establecer el módulo de configuración de Django por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecoalerta.settings')

app = Celery('ecoalerta')

# Configuración usando namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tareas desde todas las apps instaladas
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de prueba para verificar que Celery funciona"""
    print(f'Request: {self.request!r}')
