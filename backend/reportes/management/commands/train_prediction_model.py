from django.core.management.base import BaseCommand, CommandError

from reportes.ml import ReportResolutionPredictor
from reportes.ml.exceptions import PredictionModelNotReady


class Command(BaseCommand):
    help = "Entrena y guarda el modelo local de predicción de resolución de reportes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-samples",
            type=int,
            default=30,
            help="Cantidad mínima de reportes para entrenar el modelo.",
        )
        parser.add_argument(
            "--no-save",
            action="store_true",
            help="No persiste el modelo entrenado en disco (solo útil para pruebas).",
        )

    def handle(self, *args, **options):
        min_samples = options["min_samples"]
        save_artifact = not options["no_save"]

        try:
            predictor = ReportResolutionPredictor.train_from_queryset(
                min_samples=min_samples,
                save_artifact=save_artifact,
            )
        except PredictionModelNotReady as exc:
            raise CommandError(str(exc)) from exc

        metadata = predictor.metadata
        saved = "sí" if save_artifact else "no"

        self.stdout.write(
            self.style.SUCCESS(
                "Modelo entrenado correctamente "
                f"(muestras={metadata.get('num_samples')}, "
                f"tasa_resuelto={metadata.get('resolved_rate'):.2f}, "
                f"guardado={saved})."
            )
        )

