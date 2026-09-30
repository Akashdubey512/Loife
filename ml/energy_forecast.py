"""
reServe AI - Energy Forecasting Engine (Phase 8 New Module)

Predicts facility energy consumption using a LightGBM model trained on the
UCI Appliances Energy Prediction dataset.

If no trained model is available, returns a simple estimation based on
average energy per square meter.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "energy" / "energy_model.joblib"
META_PATH = PROJECT_ROOT / "models" / "energy" / "energy_model_metadata.json"

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

        logger.info(f"Loaded trained energy model: {_trained_version}")
except Exception as e:
    logger.warning(f"Could not load trained energy model: {e}")
    _trained_model = None

IS_TRAINED_MODEL = _trained_model is not None
ENGINE_TYPE = "trained" if IS_TRAINED_MODEL else "estimation"
ENGINE_VERSION = _trained_version if IS_TRAINED_MODEL else "estimation-v1.0"


class EnergyForecastingEngine:
    """
    Facility energy consumption forecasting engine.
    Uses trained model when available; provides estimation fallback.
    """

    def predict(
        self,
        kitchen_id: int = 1,
        temperature_indoor: float = 22.0,
        temperature_outdoor: float = 25.0,
        humidity_indoor: float = 45.0,
        humidity_outdoor: float = 60.0,
        wind_speed: float = 3.0,
        visibility: float = 40.0,
        tdewpoint: float = 5.0,
        press_mm_hg: float = 755.0,
        lights: float = 0.0,
        area_sqm: float = 200.0,
        **kwargs,
    ) -> Dict[str, Any]:
        """Predict energy consumption (Wh) for the facility."""
        fallback_used = False

        if IS_TRAINED_MODEL and _trained_model is not None:
            try:
                import numpy as np

                features = {}
                for col in _trained_features:
                    col_lower = col.lower()
                    if "lights" in col_lower:
                        features[col] = lights
                    elif "t1" in col_lower or ("t" in col_lower and "1" in col):
                        features[col] = temperature_indoor
                    elif "rh_1" in col_lower:
                        features[col] = humidity_indoor
                    elif "t_out" in col_lower or "t6" in col_lower:
                        features[col] = temperature_outdoor
                    elif "rh_out" in col_lower or "rh_6" in col_lower:
                        features[col] = humidity_outdoor
                    elif "windspeed" in col_lower:
                        features[col] = wind_speed
                    elif "visibility" in col_lower:
                        features[col] = visibility
                    elif "tdewpoint" in col_lower:
                        features[col] = tdewpoint
                    elif "press" in col_lower:
                        features[col] = press_mm_hg
                    else:
                        features[col] = 0

                X = np.array([[features.get(col, 0) for col in _trained_features]])
                predicted = float(_trained_model.predict(X)[0])
                predicted = max(0, round(predicted, 1))

            except Exception as e:
                logger.error(f"Energy model prediction failed: {e}")
                fallback_used = True
                predicted = round(area_sqm * 0.5, 1)  # ~0.5 Wh per sqm baseline
        else:
            predicted = round(area_sqm * 0.5, 1)
            fallback_used = not IS_TRAINED_MODEL

        return {
            "kitchen_id": kitchen_id,
            "predicted_energy_wh": predicted,
            "predicted_energy_kwh": round(predicted / 1000, 3),
            "model_type": ENGINE_TYPE if not fallback_used else "estimation",
            "model_version": ENGINE_VERSION if not fallback_used else "estimation-v1.0",
            "trained": IS_TRAINED_MODEL and not fallback_used,
            "simulated": False,
            "fallback_used": fallback_used,
            "dataset_benchmark": "Appliances Energy Prediction (UCI)",
        }


energy_engine = EnergyForecastingEngine()
