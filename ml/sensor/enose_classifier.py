"""
reServe AI - E-Nose Sensor Quality Intelligence Engine

Trained Classifier:
  - Dataset: Mendeley E-nose Beef Quality Dataset (doi:10.17632/n8mc3nspfn.1)
  - Features: Temperature, Humidity, and 8 MOS gas sensors (MQ2-MQ138)
  - Target: 4 Classes (1: EXCELLENT, 2: GOOD, 3: ACCEPTABLE, 4: SPOILED)

Dual-mode architecture:
  - If trained artifact exists (models/enose/enose_model.joblib): uses real classifier
  - Fallback: rule-based sensor threshold screening
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "enose" / "enose_model.joblib"
META_PATH = PROJECT_ROOT / "models" / "enose" / "enose_model_metadata.json"

_trained_model = None
_trained_features = None
_trained_algorithm = None
_trained_version = None
_class_to_idx = None
_idx_to_class = None
_class_names = {
    1: "EXCELLENT",
    2: "GOOD",
    3: "ACCEPTABLE",
    4: "SPOILED",
}
_class_verdicts = {
    1: "SAFE_FOR_REDISTRIBUTION",
    2: "SAFE_FOR_REDISTRIBUTION",
    3: "PROCESS_IMMEDIATELY",
    4: "HAZARD_DISCARD",
}

try:
    if MODEL_PATH.exists():
        import joblib
        bundle = joblib.load(MODEL_PATH)
        _trained_model = bundle.get("model")
        _trained_features = bundle.get("feature_columns", [])
        _trained_algorithm = bundle.get("algorithm", "LightGBM")
        _class_to_idx = bundle.get("class_to_idx", {})
        _idx_to_class = bundle.get("idx_to_class", {})
        if bundle.get("class_names"):
            _class_names = bundle["class_names"]
        if bundle.get("class_verdicts"):
            _class_verdicts = bundle["class_verdicts"]

        if META_PATH.exists():
            with open(META_PATH, "r") as f:
                meta = json.load(f)
            _trained_version = meta.get("model_version", f"trained-{_trained_algorithm.lower()}-v1.0")
        else:
            _trained_version = f"trained-{_trained_algorithm.lower()}-v1.0"
        logger.info(f"Loaded trained E-nose model: {_trained_version}")
except Exception as e:
    logger.warning(f"Could not load trained E-nose model: {e}")
    _trained_model = None

IS_TRAINED_MODEL = _trained_model is not None
ENGINE_TYPE = "trained" if IS_TRAINED_MODEL else "sensor-threshold-fallback"
ENGINE_VERSION = _trained_version if IS_TRAINED_MODEL else "enose-heuristic-v1.0"


class EnoseBeefQualityEngine:
    """
    Sensor intelligence engine for beef freshness screening via MOS gas sensors.
    """

    def __init__(self):
        self.is_trained = IS_TRAINED_MODEL
        self.version = ENGINE_VERSION
        self.algorithm = _trained_algorithm or "Heuristic"
        self.features = _trained_features or [
            "Temperature", "Humidity",
            "Mq-2", "Mq-3", "Mq-4", "Mq-5",
            "Mq-135", "Mq-136", "Mq-137", "Mq-138"
        ]

    def evaluate(self, readings: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluate meat freshness quality from gas sensor readings.
        """
        # Normalize input keys (handle variations like mq2, MQ2, Mq-2)
        norm = {}
        for k, v in readings.items():
            k_clean = k.strip()
            # Standardize common variations
            k_lower = k_clean.lower().replace("-", "").replace("_", "")
            norm[k_lower] = float(v)

        def get_val(*aliases, default=0.0):
            for a in aliases:
                a_clean = a.lower().replace("-", "").replace("_", "")
                if a_clean in norm:
                    return norm[a_clean]
            return default

        temp = get_val("Temperature", "temp", default=25.0)
        humidity = get_val("Humidity", "rh", default=60.0)
        mq2 = get_val("Mq-2", "mq2", default=500.0)
        mq3 = get_val("Mq-3", "mq3", default=400.0)
        mq4 = get_val("Mq-4", "mq4", default=300.0)
        mq5 = get_val("Mq-5", "mq5", default=300.0)
        mq135 = get_val("Mq-135", "mq135", default=450.0)
        mq136 = get_val("Mq-136", "mq136", default=400.0)
        mq137 = get_val("Mq-137", "mq137", default=700.0)
        mq138 = get_val("Mq-138", "mq138", default=60.0)

        feature_df = pd.DataFrame([[
            temp, humidity, mq2, mq3, mq4, mq5, mq135, mq136, mq137, mq138
        ]], columns=self.features)

        if self.is_trained and _trained_model is not None:
            # Model inference
            try:
                pred_idx = int(_trained_model.predict(feature_df)[0])
                predicted_class = int(_idx_to_class.get(pred_idx, pred_idx + 1))
                
                # Check for predict_proba
                probs = {}
                confidence = 0.95
                if hasattr(_trained_model, "predict_proba"):
                    proba_vec = _trained_model.predict_proba(feature_df)[0]
                    for idx, prob in enumerate(proba_vec):
                        cls_num = int(_idx_to_class.get(idx, idx + 1))
                        cls_name = _class_names.get(cls_num, f"CLASS_{cls_num}")
                        probs[cls_name] = round(float(prob), 4)
                    confidence = round(float(np.max(proba_vec)), 4)

                quality_label = _class_names.get(predicted_class, f"CLASS_{predicted_class}")
                safety_verdict = _class_verdicts.get(predicted_class, "HAZARD_DISCARD")

                return {
                    "quality_class": predicted_class,
                    "quality_label": quality_label,
                    "safety_verdict": safety_verdict,
                    "confidence": confidence,
                    "class_probabilities": probs,
                    "model_type": ENGINE_TYPE,
                    "model_version": self.version,
                    "algorithm": self.algorithm,
                    "is_trained_model": True,
                    "scope": "BEEF_QUALITY_ONLY",
                    "notice": "Trained strictly on Mendeley E-nose Beef Quality Dataset (doi:10.17632/n8mc3nspfn.1). Human inspection required.",
                }
            except Exception as e:
                logger.error(f"Inference error with trained model: {e}")
                # Fall through to heuristic

        # Heuristic fallback
        # TVC threshold approximation based on sensor intensity
        volatile_load = (mq2 + mq3 + mq135 + mq137) / 4.0
        if volatile_load < 400.0 and temp < 10.0:
            quality_class = 1
        elif volatile_load < 550.0:
            quality_class = 2
        elif volatile_load < 700.0:
            quality_class = 3
        else:
            quality_class = 4

        quality_label = _class_names.get(quality_class, "SPOILED")
        safety_verdict = _class_verdicts.get(quality_class, "HAZARD_DISCARD")

        return {
            "quality_class": quality_class,
            "quality_label": quality_label,
            "safety_verdict": safety_verdict,
            "confidence": 0.70,
            "class_probabilities": {
                quality_label: 0.70,
            },
            "model_type": "heuristic",
            "model_version": "enose-heuristic-v1.0",
            "algorithm": "SensorThresholdRule",
            "is_trained_model": False,
            "scope": "BEEF_QUALITY_ONLY",
            "notice": "Rule-based fallback. Human inspection required.",
        }


enose_engine = EnoseBeefQualityEngine()
