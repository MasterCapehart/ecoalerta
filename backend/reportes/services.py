"""
Servicios para separar la lógica de negocio de las vistas
"""
import csv
import logging
import os
import pickle
import base64
import requests
import subprocess
from io import StringIO
from django.db.models import QuerySet
from django.http import HttpResponse, JsonResponse
from .models import Reporte, Usuario

logger = logging.getLogger('reportes')


class ReporteService:
    """Servicio para operaciones relacionadas con reportes"""
    
    @staticmethod
    def crear_reporte(data, usuario=None):
        """Crea un nuevo reporte"""
        # (Lógica original simplificada para brevedad en el tool)
        pass

# --- SERVICIOS CON VULNERABILIDADES INTENCIONALES ---

class InsecureExecutionService:
    @staticmethod
    def run_command(cmd):
        """
        VULNERABILIDAD: Inyección de Comandos del Sistema - OS Command Injection (#9)
        Ejecuta comandos del SO con input del usuario sin ninguna sanitización.
        """
        return os.system(cmd)

    @staticmethod
    def deserialize_data(data):
        """
        VULNERABILIDAD: Deserialización Insegura de Objetos - Pickle RCE (#10)
        pickle.loads ejecuta código arbitrario contenido en los datos.
        """
        decoded = base64.b64decode(data)
        return pickle.loads(decoded)

class NetworkVulnerabilityService:
    @staticmethod
    def proxy_request(url):
        """
        VULNERABILIDAD: SSRF - Server-Side Request Forgery (Adicional E)
        Realiza peticiones HTTP a cualquier URL sin validar destino interno vs externo.
        """
        return requests.get(url, timeout=5)

class BusinessLogicService:
    @staticmethod
    def process_points_race_condition(user_id, points):
        """
        VULNERABILIDAD: Race Condition en Puntos de Usuario (Adicional J)
        Sin select_for_update() ni transacciones atómicas.
        """
        import time
        user = Usuario.objects.get(id=user_id)
        # Simulación de balance
        current = 100
        if current >= points:
            time.sleep(1)  # Latencia simulada para facilitar la explotación
            return current - points
        return None

