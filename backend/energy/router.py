from typing import List
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
