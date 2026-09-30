"""
reServe AI - Predictive Equipment Maintenance Engine (Phase 8 Upgrade)

DUAL-MODE ENGINE:
  - If trained model exists (models/maintenance/maintenance_model.joblib):
    uses real LightGBM/XGBoost/RF classifier trained on AI4I 2020 data
  - Otherwise: falls back to threshold-based boundary checks (Phase 7)

All API responses honestly report model_type, model_version, trained, and fallback_used.
"""

import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "maintenance" / "maintenance_model.joblib"
META_PATH = PROJECT_ROOT / "models" / "maintenance" / "maintenance_model_metadata.json"

# ──────────────────────────────────────────────────────────
# Attempt to load trained model
# ──────────────────────────────────────────────────────────
_trained_model = None
_trained_features = None
_trained_algorithm = None
_trained_version = None

try:
    if MODEL_PATH.exists():
        import joblib, json
        bundle = joblib.load(MODEL_PATH)
        _trained_model = bundle["model"]
        _trained_features = bundle["feature_columns"]
        _trained_algorithm = bundle["algorithm"]

        if META_PATH.exists():
            with open(META_PATH) as f:
                meta = json.load(f)
            _trained_version = meta.get("model_version", f"trained-{_trained_algorithm.lower()}-v1.0")
        else:
            _trained_version = f"trained-{_trained_algorithm.lower()}-v1.0"

        logger.info(f"Loaded trained maintenance model: {_trained_version}")
except Exception as e:
    logger.warning(f"Could not load trained maintenance model: {e}. Falling back to thresholds.")
    _trained_model = None

IS_TRAINED_MODEL = _trained_model is not None
ENGINE_TYPE = "trained" if IS_TRAINED_MODEL else "threshold-based"
ENGINE_VERSION = _trained_version if IS_TRAINED_MODEL else "threshold-v1.0"


class PredictiveMaintenanceEngine:
    """
    Dual-mode predictive maintenance engine.
    Uses trained classifier when available; falls back to AI4I 2020
    physical boundary checks otherwise.
    """

    def _trained_evaluate(
        self,
        air_temp_k: float,
        process_temp_k: float,
        rotational_speed_rpm: float,
        torque_nm: float,
        tool_wear_min: float,
        product_type: str = "M",
    ) -> Dict[str, Any]:
        """Evaluate using trained model."""
        import numpy as np

        # Build feature vector matching training columns
        type_map = {"L": 0, "M": 1, "H": 2}
        features = {}
        for col in _trained_features:
            col_lower = col.lower()
            if "air temp" in col_lower:
                features[col] = air_temp_k
            elif "process temp" in col_lower:
                features[col] = process_temp_k
            elif "rotational" in col_lower:
                features[col] = rotational_speed_rpm
            elif "torque" in col_lower:
                features[col] = torque_nm
            elif "tool wear" in col_lower:
                features[col] = tool_wear_min
            elif "encoded" in col_lower or "type" in col_lower:
                features[col] = type_map.get(product_type.upper(), 1)
            else:
                features[col] = 0

        X = np.array([[features[col] for col in _trained_features]])
        prediction = int(_trained_model.predict(X)[0])
        proba = float(_trained_model.predict_proba(X)[0][1])

        # Determine failure type from sensor readings (interpretive)
        temp_diff = process_temp_k - air_temp_k
        power_w = rotational_speed_rpm * torque_nm * (2 * 3.14159 / 60)
        overstrain = tool_wear_min * torque_nm

        if prediction == 1:
            if temp_diff < 8.6:
                failure_type = "Heat Dissipation Failure (HDF)"
                recommendation = "Check cooling fan airflow and clean heat-sink fins immediately."
            elif power_w < 3500 or power_w > 9000:
                failure_type = "Power Failure (PWF)"
                recommendation = "Motor power draw is outside normal operational boundaries. Inspect electrical drive."
            elif overstrain > 11000:
                failure_type = "Overstrain Failure (OSF)"
                recommendation = "High mechanical load and bearing wear detected. Relieve compressor head pressure."
            elif tool_wear_min > 200:
                failure_type = "Tool Wear Failure (TWF)"
                recommendation = "Component operating hours exceeded maximum service lifespan. Schedule replacement."
            else:
                failure_type = "General Failure Risk"
                recommendation = "Model detected anomalous sensor pattern. Schedule preventive inspection."
            status = "CRITICAL_SHUTDOWN" if proba > 0.7 else "MAINTENANCE_REQUIRED"
        else:
            failure_type = "None"
            status = "HEALTHY"
            recommendation = "Standard operation. All sensor readings within normal range."

        return {
            "failure_probability": round(proba, 4),
            "failure_type": failure_type,
            "status": status,
            "recommended_action": recommendation,
            "power_w": round(power_w, 1),
            "temp_diff_k": round(temp_diff, 1),
        }

    def _threshold_evaluate(
        self,
        air_temp_k: float,
        process_temp_k: float,
        rotational_speed_rpm: float,
        torque_nm: float,
        tool_wear_min: float,
    ) -> Dict[str, Any]:
        """Threshold-based evaluation (Phase 7 logic preserved)."""
        temp_diff = process_temp_k - air_temp_k
        power_w = rotational_speed_rpm * torque_nm * (2 * 3.14159 / 60)
        overstrain_product = tool_wear_min * torque_nm

        failure_probability = 0.02
        failure_type = "None"
        status = "HEALTHY"
        recommendation = "Standard operation. Normal cycle detected."

        # 1. Heat Dissipation Failure (HDF)
        if temp_diff < 8.6 and rotational_speed_rpm < 1380:
            failure_probability = 0.78
            failure_type = "Heat Dissipation Failure (HDF)"
            status = "MAINTENANCE_REQUIRED"
            recommendation = "Check cooling fan airflow and clean heat-sink fins immediately."

        # 2. Power Failure (PWF)
        elif power_w < 3500 or power_w > 9000:
            failure_probability = 0.85
            failure_type = "Power Failure (PWF)"
            status = "CRITICAL_SHUTDOWN"
            recommendation = "Motor power draw is outside normal operational boundaries. Inspect electrical drive."

        # 3. Overstrain Failure (OSF)
        elif overstrain_product > 11000:
            failure_probability = 0.72
            failure_type = "Overstrain Failure (OSF)"
            status = "MAINTENANCE_REQUIRED"
            recommendation = "High mechanical load and bearing wear detected. Relieve compressor head pressure."

        # 4. Tool Wear Failure (TWF)
        elif tool_wear_min > 200:
            failure_probability = 0.65
            failure_type = "Tool Wear Failure (TWF)"
            status = "MAINTENANCE_REQUIRED"
            recommendation = "Component operating hours exceeded maximum service lifespan. Schedule replacement."

        return {
            "failure_probability": round(failure_probability, 2),
            "failure_type": failure_type,
            "status": status,
            "recommended_action": recommendation,
            "power_w": round(power_w, 1),
            "temp_diff_k": round(temp_diff, 1),
        }

    def evaluate_machine(
        self,
        machine_id: str,
        machine_type: str,
        air_temp_k: float = 300.0,
        process_temp_k: float = 310.0,
        rotational_speed_rpm: float = 1500.0,
        torque_nm: float = 40.0,
        tool_wear_min: float = 15.0
    ) -> Dict[str, Any]:
        """
        Evaluates machine health. Uses trained model when available,
        falls back to threshold-based checks otherwise.
        """
        fallback_used = False

        if IS_TRAINED_MODEL and _trained_model is not None:
            try:
                result = self._trained_evaluate(
                    air_temp_k, process_temp_k, rotational_speed_rpm,
                    torque_nm, tool_wear_min
                )
            except Exception as e:
                logger.error(f"Trained maintenance model failed, falling back: {e}")
                fallback_used = True
                result = self._threshold_evaluate(
                    air_temp_k, process_temp_k, rotational_speed_rpm,
                    torque_nm, tool_wear_min
                )
        else:
            result = self._threshold_evaluate(
                air_temp_k, process_temp_k, rotational_speed_rpm,
                torque_nm, tool_wear_min
            )

        return {
            "machine_id": machine_id,
            "machine_type": machine_type,
            **result,
            "model_type": ENGINE_TYPE if not fallback_used else "threshold-based",
            "model_version": ENGINE_VERSION if not fallback_used else "threshold-v1.0",
            "trained": IS_TRAINED_MODEL and not fallback_used,
            "fallback_used": fallback_used,
            "dataset_benchmark": "AI4I 2020 Predictive Maintenance (UCI)"
        }

maintenance_engine = PredictiveMaintenanceEngine()
