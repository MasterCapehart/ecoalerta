from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import joblib
import pandas as pd
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from reportes.models import Reporte

from .constants import MODEL_FILE, MODEL_DIR
from .exceptions import PredictionModelNotFound, PredictionModelNotReady


RESOLVED_STATES = {"resuelto", "cerrado"}

# Caché simple para estadísticas de resolución
_resolution_stats_cache: Optional[Dict[str, Any]] = None
_resolution_stats_cache_timestamp: Optional[float] = None
CACHE_TTL_SECONDS = 300  # Cache válido por 5 minutos


@dataclass
class PredictionResult:
    probability: float
    estimated_days: int
    risk_level: str
    source: str
    metadata: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "probability": self.probability,
            "estimated_resolution_days": self.estimated_days,
            "risk_level": self.risk_level,
            "source": self.source,
            "metadata": self.metadata,
        }


class ReportResolutionPredictor:
    """Helper that trains, loads and serves resolution predictions."""

    NUMERIC_FEATURES = [
        "lat",
        "lng",
        "descripcion_len",
        "dias_abierto",
        "tiene_foto",
    ]
    CATEGORICAL_FEATURES = ["categoria_id", "estado"]

    def __init__(self, pipeline: Pipeline, metadata: Optional[Dict[str, Any]] = None):
        self.pipeline = pipeline
        self.metadata = metadata or {}

    # ------------------------------------------------------------------ #
    # Persistence helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def exists(cls) -> bool:
        return MODEL_FILE.exists()

    @classmethod
    def load(cls) -> "ReportResolutionPredictor":
        if not MODEL_FILE.exists():
            raise PredictionModelNotFound("Model artifact not found")
        payload = joblib.load(MODEL_FILE)
        return cls(pipeline=payload["model"], metadata=payload.get("metadata", {}))

    @classmethod
    def train_from_queryset(
        cls,
        queryset: Optional[Iterable[Reporte]] = None,
        *,
        min_samples: int = 30,
        save_artifact: bool = True,
    ) -> "ReportResolutionPredictor":
        queryset = queryset or Reporte.objects.select_related("categoria").all()

        records: list[Dict[str, Any]] = []
        targets: list[int] = []
        now = timezone.now()

        for reporte in queryset:
            feature_row = cls._build_feature_row_from_instance(reporte, reference_dt=now)
            if feature_row is None:
                continue
            records.append(feature_row)
            targets.append(1 if reporte.estado in RESOLVED_STATES else 0)

        if len(records) < min_samples:
            raise PredictionModelNotReady(
                f"Insufficient samples to train model (got {len(records)}, need {min_samples})"
            )

        if len(set(targets)) < 2:
            raise PredictionModelNotReady(
                "All samples belong to the same class; cannot train classifier"
            )

        df = pd.DataFrame(records)

        preprocess = ColumnTransformer(
            transformers=[
                ("numeric", StandardScaler(), cls.NUMERIC_FEATURES),
                (
                    "categorical",
                    OneHotEncoder(handle_unknown="ignore"),
                    cls.CATEGORICAL_FEATURES,
                ),
            ]
        )

        pipeline = Pipeline(
            steps=[
                ("preprocess", preprocess),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                    ),
                ),
            ]
        )

        pipeline.fit(df, targets)

        metadata = {
            "trained_at": now.isoformat(),
            "num_samples": len(records),
            "resolved_rate": float(sum(targets)) / len(targets),
            "features": cls.NUMERIC_FEATURES + cls.CATEGORICAL_FEATURES,
        }

        if save_artifact:
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            joblib.dump({"model": pipeline, "metadata": metadata}, MODEL_FILE)

        return cls(pipeline=pipeline, metadata=metadata)

    # ------------------------------------------------------------------ #
    # Feature builders
    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_feature_row_from_instance(
        reporte: Reporte, reference_dt: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        reference_dt = reference_dt or timezone.now()

        if not reporte.fecha_creacion:
            return None

        return {
            "categoria_id": reporte.categoria_id or 0,
            "estado": reporte.estado,
            "lat": reporte.ubicacion_lat if reporte.ubicacion_lat is not None else 0.0,
            "lng": reporte.ubicacion_lng if reporte.ubicacion_lng is not None else 0.0,
            "descripcion_len": len((reporte.descripcion or "").strip()),
            "dias_abierto": max(
                (reference_dt - reporte.fecha_creacion).total_seconds() / 86400.0, 0.0
            ),
            "tiene_foto": 1.0 if bool(reporte.foto) else 0.0,
        }

    @staticmethod
    def _build_features_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        descripcion = payload.get("descripcion") or ""
        dias_abierto = payload.get("dias_abierto")

        if dias_abierto is None and payload.get("fecha_creacion"):
            fecha = parse_datetime(payload["fecha_creacion"])
            if fecha is not None:
                if timezone.is_naive(fecha):
                    fecha = timezone.make_aware(fecha, timezone=timezone.utc)
                # Redondear a días completos para mayor consistencia
                dias_abierto = max(
                    int((timezone.now() - fecha).total_seconds() / 86400.0),
                    0,
                )
            else:
                dias_abierto = 0

        # Asegurar que dias_abierto sea un entero (días completos)
        if dias_abierto is not None:
            dias_abierto = int(dias_abierto)

        return {
            "categoria_id": payload.get("categoria_id") or 0,
            "estado": payload.get("estado") or "nuevo",
            "lat": payload.get("lat") or 0.0,
            "lng": payload.get("lng") or 0.0,
            "descripcion_len": len(descripcion.strip()),
            "dias_abierto": float(dias_abierto) if dias_abierto is not None else 0.0,
            "tiene_foto": 1.0 if payload.get("tiene_foto") else 0.0,
        }

    # ------------------------------------------------------------------ #
    # Prediction interface
    # ------------------------------------------------------------------ #
    def predict_from_payload(self, payload: Dict[str, Any]) -> PredictionResult:
        features = self._build_features_from_payload(payload)
        df = pd.DataFrame([features])
        probability = float(self.pipeline.predict_proba(df)[0][1])
        risk_level = self._risk_level(probability)
        estimated_days = self._estimated_days(probability, features["dias_abierto"])
        return PredictionResult(
            probability=probability,
            estimated_days=estimated_days,
            risk_level=risk_level,
            source="ml-model",
            metadata=self.metadata,
        )

    # ------------------------------------------------------------------ #
    # Fallback heuristics when model is unavailable
    # ------------------------------------------------------------------ #
    @staticmethod
    def fallback_prediction(payload: Dict[str, Any]) -> PredictionResult:
        stats = ReportResolutionPredictor._compute_resolution_stats()
        categoria_id = payload.get("categoria_id")
        category_ratio = stats["category_ratios"].get(categoria_id)
        probability = category_ratio or stats["global_ratio"]
        probability = float(probability)

        risk_level = ReportResolutionPredictor._risk_level(probability)
        estimated_days = ReportResolutionPredictor._estimated_days(
            probability, payload.get("dias_abierto", 0)
        )

        metadata = {
            "source": "heuristic",
            "samples_considered": stats["sample_size"],
            "category_ratio_used": category_ratio,
        }

        return PredictionResult(
            probability=probability,
            estimated_days=estimated_days,
            risk_level=risk_level,
            source="heuristic",
            metadata=metadata,
        )

    @staticmethod
    def _compute_resolution_stats() -> Dict[str, Any]:
        """
        Calcula estadísticas de resolución con caché para evitar recálculos constantes.
        El caché es válido por 5 minutos para balancear consistencia y actualización.
        """
        global _resolution_stats_cache, _resolution_stats_cache_timestamp
        
        import time
        current_time = time.time()
        
        # Usar caché si existe y no ha expirado
        if (_resolution_stats_cache is not None and 
            _resolution_stats_cache_timestamp is not None and
            (current_time - _resolution_stats_cache_timestamp) < CACHE_TTL_SECONDS):
            return _resolution_stats_cache
        
        # Calcular nuevas estadísticas
        qs = (
            Reporte.objects.values("categoria_id")
            .annotate(
                total=Count("id"),
                resolved=Count(
                    "id", filter=Q(estado__in=RESOLVED_STATES)
                ),
            )
            .order_by()
        )

        category_ratios: Dict[Optional[int], float] = {}
        total_samples = 0
        total_resolved = 0

        for row in qs:
            total_samples += row["total"]
            total_resolved += row["resolved"]
            if row["total"]:
                category_ratios[row["categoria_id"]] = row["resolved"] / row["total"]

        global_ratio = (total_resolved / total_samples) if total_samples else 0.5

        stats = {
            "category_ratios": category_ratios,
            "global_ratio": global_ratio,
            "sample_size": total_samples,
        }
        
        # Actualizar caché
        _resolution_stats_cache = stats
        _resolution_stats_cache_timestamp = current_time
        
        return stats

    # ------------------------------------------------------------------ #
    # Utility helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _risk_level(probability: float) -> str:
        if probability >= 0.75:
            return "alto"
        if probability >= 0.45:
            return "medio"
        return "bajo"

    @staticmethod
    def _estimated_days(probability: float, dias_abierto: float) -> int:
        base_days = max(1.0, 14.0 * (1 - probability))
        projected = base_days - dias_abierto
        return max(int(round(projected)) + 1, 1)

