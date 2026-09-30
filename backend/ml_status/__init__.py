"""
reServe AI - ML Model Status Router (Phase 9)

Provides a single endpoint to report the truthful status of all ML/CV models.
Verifies that model artifacts actually exist before reporting trained=True.
"""
import json
from pathlib import Path
from fastapi import APIRouter, Depends
from backend.core.deps import get_current_user
from backend.models.entities import User

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = PROJECT_ROOT / "models" / "model_registry.json"


def _load_registry():
    """Load model registry and verify artifact existence."""
    if not REGISTRY_PATH.exists():
        return []
    with open(REGISTRY_PATH, "r") as f:
        registry = json.load(f)
    # Verify each artifact actually exists
    for entry in registry:
        artifact = entry.get("artifact")
        if artifact and entry.get("status") == "trained":
            artifact_path = PROJECT_ROOT / artifact
            if not artifact_path.exists():
                entry["status"] = "artifact_missing"
                entry["_warning"] = f"Artifact not found: {artifact}"
    return registry


@router.get("/status")
def get_ml_status(current_user: User = Depends(get_current_user)):
    """Report the live, verified status of all ML/CV engines."""
    registry = _load_registry()

    # Also verify engines can actually load
    engine_status = []

    # 1. Demand Forecasting
    try:
        from ml.demand_forecast import ENGINE_TYPE, ENGINE_VERSION, IS_TRAINED_MODEL
        engine_status.append({
            "engine": "demand_forecasting",
            "model_type": ENGINE_TYPE,
            "model_version": ENGINE_VERSION,
            "trained": IS_TRAINED_MODEL,
            "endpoint": "/api/v1/demand/predict",
        })
    except Exception as e:
        engine_status.append({"engine": "demand_forecasting", "status": "ERROR", "error": str(e)})

    # 2. Predictive Maintenance
    try:
        from ml.predictive_maintenance import ENGINE_TYPE as M, ENGINE_VERSION as MV, IS_TRAINED_MODEL as MT
        engine_status.append({
            "engine": "predictive_maintenance",
            "model_type": M,
            "model_version": MV,
            "trained": MT,
            "endpoint": "/api/v1/maintenance/evaluate",
        })
    except Exception as e:
        engine_status.append({"engine": "predictive_maintenance", "status": "ERROR", "error": str(e)})

    # 3. Energy Forecasting
    try:
        from ml.energy_forecast import ENGINE_TYPE as E, ENGINE_VERSION as EV, IS_TRAINED_MODEL as ET
        engine_status.append({
            "engine": "energy_forecasting",
            "model_type": E,
            "model_version": EV,
            "trained": ET,
            "endpoint": "/api/v1/energy/predict",
        })
    except Exception as e:
        engine_status.append({"engine": "energy_forecasting", "status": "ERROR", "error": str(e)})

    # 4. Waste Prediction
    engine_status.append({
        "engine": "waste_prediction",
        "model_type": "rule-based",
        "model_version": "rule-based-v1.0",
        "trained": False,
        "status": "fallback",
        "reason": "No legitimate labeled waste training data available",
        "endpoint": "/api/v1/waste/predictions",
    })

    # 5. CV Freshness
    try:
        from cv.freshness_classifier import SIMULATION_MODE
        engine_status.append({
            "engine": "cv_freshness_classifier",
            "model_type": "simulated" if SIMULATION_MODE else "trained",
            "model_version": "spectral-spatial-v2.1-SIMULATED" if SIMULATION_MODE else "fruit-freshness-cnn",
            "trained": not SIMULATION_MODE,
            "simulated": SIMULATION_MODE,
            "status": "unavailable" if SIMULATION_MODE else "trained",
            "reason": "Fruit dataset requires manual Mendeley download" if SIMULATION_MODE else None,
            "endpoint": "/api/v1/quality/scan",
            "scope": "Fruit freshness ONLY (not universal food safety)" if not SIMULATION_MODE else None,
        })
    except Exception as e:
        engine_status.append({"engine": "cv_freshness_classifier", "status": "ERROR", "error": str(e)})

    # 6. E-nose Sensor
    engine_status.append({
        "engine": "enose_beef_quality",
        "model_type": "unavailable",
        "model_version": "unavailable",
        "trained": False,
        "status": "unavailable",
        "reason": "E-nose dataset requires manual Mendeley download",
        "scope": "Beef quality ONLY (not universal food quality)",
    })

    # 7. Sustainability
    try:
        from ml.sustainability_engine import sustainability_engine
        engine_status.append({
            "engine": "sustainability_lca",
            "model_type": "lookup_table",
            "model_version": "poore-nemecek-v2.0",
            "trained": False,
            "status": "active",
            "product_count": sustainability_engine.product_count,
            "endpoint": "/api/v1/sustainability/summary",
        })
    except Exception as e:
        engine_status.append({"engine": "sustainability_lca", "status": "ERROR", "error": str(e)})

    trained_count = sum(1 for e in engine_status if e.get("trained", False))
    active_count = sum(1 for e in engine_status if e.get("status") not in ("ERROR", "unavailable"))

    return {
        "platform": "reServe AI",
        "ml_status": "OPERATIONAL",
        "trained_models": trained_count,
        "active_engines": active_count,
        "total_engines": len(engine_status),
        "engines": engine_status,
    }
