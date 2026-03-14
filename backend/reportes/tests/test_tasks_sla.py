from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from reportes.models import CategoriaResiduo, Notificacion, Reporte
from reportes.tasks import verificar_sla_reportes
from .test_predictions import SQLITE_TEST_DB

User = get_user_model()


@override_settings(DATABASES=SQLITE_TEST_DB)
class VerificarSLAReportesTests(TestCase):
    def setUp(self):
        self.categoria = CategoriaResiduo.objects.create(nombre='Orgánico')
        self.inspector = User.objects.create_user(
            username='insp_sla',
            password='testpass123',
            tipo='inspector',
            email='insp@example.com',
        )
        self.admin = User.objects.create_user(
            username='admin_sla',
            password='testpass123',
            tipo='admin',
            email='admin@example.com',
        )

    @patch('reportes.notification_service.NotificationService.send_email_notification', return_value=True)
    def test_escalado_automatico_para_reportes_excedidos(self, _mock_send):
        reporte = Reporte.objects.create(
            categoria=self.categoria,
            estado='proceso',
            asignado_a=self.inspector,
            fecha_limite_resolucion=timezone.now() - timedelta(hours=2),
        )

        result = verificar_sla_reportes()

        reporte.refresh_from_db()
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['reportes_escalados'], 1)
        self.assertEqual(reporte.prioridad, 'urgente')
        self.assertTrue(reporte.sla_escalado)
        self.assertIsNotNone(reporte.sla_escalado_at)
        self.assertTrue(Notificacion.objects.filter(reporte=reporte, titulo='SLA excedido y escalado').exists())
