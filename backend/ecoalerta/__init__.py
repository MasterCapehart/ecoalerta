# UrbanAlert Backend
# NO importar nada relacionado con GeoDjango aquí

# Importar Celery cuando Django esté listo
from .celery import app as celery_app

__all__ = ('celery_app',)
