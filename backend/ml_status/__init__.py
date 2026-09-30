"""
reServe AI - ML Model Status Router (Phase 8)

Provides a single endpoint to report the status of all ML/CV models
in the system: which are trained, which use heuristics, versions, datasets.
"""
from fastapi import APIRouter, Depends
from backend.core.deps import get_current_user
from backend.models.entities import User

router = APIRouter()


@router.get("/status")
def get_ml_status(current_user: User = Depends(get_current_user)):
    """Report the live status of all ML/CV engines in the system."""
    engines = []

    # 1. Demand Forecasting
    try:
        from ml.demand_forecast import ENGINE_TYPE, ENGINE_VERSION, IS_TRAINED_MODEL
        engines.append({
            "engine": "demand_forecasting",
            "model_type": ENGINE_TYPE,
            "model_version": ENGINE_VERSION,
            "trained": IS_TRAINED_MODEL,
            "endpoint": "/api/v1/demand/predict",
            "dataset": "Genpact Food Demand Forecasting",
        })
    except Exception as e:
        engines.append({"engine": "demand_forecasting", "status": "ERROR", "error": str(e)})

    # 2. Waste Prediction
    try:
        from ml.waste_predictor import waste_engine
        engines.append({
            "engine": "waste_prediction",
            "model_type": "rule-based",
            "model_version": "rule-based-v1.0",
            "trained": False,
            "endpoint": "/api/v1/waste/predictions",
            "dataset": "None (rule-based)",
        })
    except Exception as e:
        engines.append({"engine": "waste_prediction", "status": "ERROR", "error": str(e)})

    # 3. CV Freshness
    try:
        from cv.freshness_classifier import SIMULATION_MODE
        engines.append({
            "engine": "cv_freshness_classifier",
            "model_type": "simulated" if SIMULATION_MODE else "trained",
            "model_version": "EfficientNet-B0 (SIMULATED)" if SIMULATION_MODE else "trained",
            "trained": not SIMULATION_MODE,
            "simulated": SIMULATION_MODE,
            "endpoint": "/api/v1/quality/scan",
            "dataset": "Fresh & Rotten Fruits (Mendeley)" if not SIMULATION_MODE else "None (simulated)",
        })
    except Exception as e:
        engines.append({"engine": "cv_freshness_classifier", "status": "ERROR", "error": str(e)})

    # 4. Predictive Maintenance
    try:
        from ml.predictive_maintenance import ENGINE_TYPE as M_TYPE, ENGINE_VERSION as M_VER, IS_TRAINED_MODEL as M_TRAINED
        engines.append({
            "engine": "predictive_maintenance",
            "model_type": M_TYPE,
            "model_version": M_VER,
            "trained": M_TRAINED,
            "endpoint": "/api/v1/maintenance/evaluate",
            "dataset": "AI4I 2020 Predictive Maintenance (UCI)",
        })
    except Exception as e:
        engines.append({"engine": "predictive_maintenance", "status": "ERROR", "error": str(e)})

    # 5. Energy Forecasting
    try:
        from ml.energy_forecast import ENGINE_TYPE as E_TYPE, ENGINE_VERSION as E_VER, IS_TRAINED_MODEL as E_TRAINED
        engines.append({
            "engine": "energy_forecasting",
            "model_type": E_TYPE,
            "model_version": E_VER,
            "trained": E_TRAINED,
            "endpoint": "/api/v1/energy/predict",
            "dataset": "Appliances Energy Prediction (UCI)",
        })
    except Exception as e:
        engines.append({"engine": "energy_forecasting", "status": "ERROR", "error": str(e)})

    # 6. Sustainability
    try:
        from ml.sustainability_engine import sustainability_engine
        engines.append({
            "engine": "sustainability_lca",
            "model_type": "lookup_table",
            "model_version": "poore-nemecek-v2.0",
            "trained": False,
            "product_count": sustainability_engine.product_count,
            "endpoint": "/api/v1/sustainability/summary",
            "dataset": "Poore & Nemecek (2018) Science Table S2",
        })
    except Exception as e:
        engines.append({"engine": "sustainability_lca", "status": "ERROR", "error": str(e)})

    # 7. Logistics
    try:
        engines.append({
            "engine": "logistics_optimizer",
            "model_type": "heuristic",
            "model_version": "greedy-nearest-neighbor-v1.0",
            "trained": False,
            "endpoint": "/api/v1/logistics/optimize",
            "dataset": "CVRPLIB (benchmark, pending)",
        })
    except Exception as e:
        engines.append({"engine": "logistics_optimizer", "status": "ERROR", "error": str(e)})

    trained_count = sum(1 for e in engines if e.get("trained", False))
    total_count = len(engines)

    return {
        "platform": "reServe AI",
        "ml_status": "OPERATIONAL",
        "trained_models": trained_count,
        "total_engines": total_count,
        "engines": engines,
    }
