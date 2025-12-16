from pathlib import Path

from django.conf import settings

# Directory where trained models and metadata are stored locally
MODEL_DIR = Path(settings.BASE_DIR) / "reportes" / "ml" / "artifacts"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILE = MODEL_DIR / "report_resolution_model.joblib"

