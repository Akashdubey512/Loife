from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.entities import EnergyConsumption, WaterConsumption, User

router = APIRouter()

class EnergySummary(BaseModel):
    total_power_kwh_today: float
    total_cost_inr_today: float
    water_liters_today: float
    efficiency_score_pct: float

class EnergyPredictionRequest(BaseModel):
    kitchen_id: int = 1
    temperature_indoor: float = 22.0
    temperature_outdoor: float = 25.0
    humidity_indoor: float = 45.0
    humidity_outdoor: float = 60.0
    area_sqm: float = 200.0

class EnergyPredictionResponse(BaseModel):
    kitchen_id: int
    predicted_energy_wh: float
    predicted_energy_kwh: float
    model_type: str
    model_version: str
    trained: bool
    simulated: bool
    fallback_used: bool
    dataset_benchmark: str

@router.get("/summary", response_model=EnergySummary)
def get_energy_summary(
    kitchen_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return EnergySummary(
        total_power_kwh_today=312.4,
        total_cost_inr_today=2499.2,
        water_liters_today=1450.0,
        efficiency_score_pct=91.5
    )

@router.post("/predict", response_model=EnergyPredictionResponse)
def predict_energy(
    request: EnergyPredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """Predict energy consumption using trained ML model (Appliances Energy dataset)."""
    from ml.energy_forecast import energy_engine
    result = energy_engine.predict(
        kitchen_id=request.kitchen_id,
        temperature_indoor=request.temperature_indoor,
        temperature_outdoor=request.temperature_outdoor,
        humidity_indoor=request.humidity_indoor,
        humidity_outdoor=request.humidity_outdoor,
        area_sqm=request.area_sqm,
    )
    return EnergyPredictionResponse(**result)

