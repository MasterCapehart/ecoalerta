from unittest.mock import patch

from django.test import TestCase, override_settings

from reportes.models import CategoriaResiduo, Reporte
from reportes.serializers import ReportePredictionRequestSerializer, ReporteSerializer
from reportes.ml import ReportResolutionPredictor
from reportes.ml.predictor import PredictionResult
from reportes.ml.exceptions import PredictionModelNotFound


SQLITE_TEST_DB = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}


@override_settings(DATABASES=SQLITE_TEST_DB)
class PredictionSerializerTests(TestCase):
    def test_to_feature_payload_builds_expected_dict(self):
        categoria = CategoriaResiduo.objects.create(nombre="Orgánicos")

        serializer = ReportePredictionRequestSerializer(
            data={
                "categoria": categoria.id,
                "estado": "nuevo",
                "lat": -33.45,
                "lng": -70.66,
                "descripcion": "Basura acumulada",
                "tiene_foto": True,
                "dias_abierto": 1.5,
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        payload = serializer.to_feature_payload()

        self.assertEqual(payload["categoria_id"], categoria.id)
        self.assertEqual(payload["estado"], "nuevo")
        self.assertEqual(payload["lat"], -33.45)
        self.assertEqual(payload["lng"], -70.66)
        self.assertEqual(payload["tiene_foto"], True)
        self.assertEqual(payload["dias_abierto"], 1.5)


@override_settings(DATABASES=SQLITE_TEST_DB)
class PredictionFallbackTests(TestCase):
    def test_fallback_prediction_returns_result(self):
        payload = {
            "categoria_id": None,
            "estado": "nuevo",
            "lat": 0,
            "lng": 0,
            "descripcion": "",
            "tiene_foto": False,
            "dias_abierto": 0,
        }

        result = ReportResolutionPredictor.fallback_prediction(payload)

        self.assertTrue(0 <= result.probability <= 1)
        self.assertIn(result.risk_level, {"alto", "medio", "bajo"})
        self.assertGreaterEqual(result.estimated_days, 1)
        self.assertEqual(result.source, "heuristic")


@override_settings(DATABASES=SQLITE_TEST_DB, DEBUG=True)
class SerializerPredictionTests(TestCase):
    def test_prediction_field_includes_fallback_data(self):
        categoria = CategoriaResiduo.objects.create(nombre="Mixtos")
        reporte = Reporte.objects.create(
            categoria=categoria,
            descripcion="Basura",
            ubicacion_lat=-33.4,
            ubicacion_lng=-70.6,
            estado="nuevo",
        )

        fake_result = PredictionResult(
            probability=0.8,
            estimated_days=2,
            risk_level="alto",
            source="heuristic",
            metadata={"num_samples": 1},
        )

        with patch("reportes.serializers._load_predictor", side_effect=PredictionModelNotFound()), patch(
            "reportes.serializers.ReportResolutionPredictor.fallback_prediction",
            return_value=fake_result,
        ):
            data = ReporteSerializer(instance=reporte).data

        self.assertIn("prediction", data)
        self.assertEqual(data["prediction"]["risk_level"], "alto")
        self.assertEqual(data["prediction"]["source"], "heuristic")

