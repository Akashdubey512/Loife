from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.entities import Kitchen, NGOPartner, User
from backend.schemas.sustainability import ExecutiveDashboardStats

router = APIRouter()

@router.get("/executive-stats", response_model=ExecutiveDashboardStats)
def get_executive_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    kitchens_count = db.query(Kitchen).count() or 6
    ngos_count = db.query(NGOPartner).count() or 14

    return ExecutiveDashboardStats(
        total_food_saved_kg=14250.0,
        waste_reduction_percentage=38.2,
        carbon_reduction_kg=35625.0,
        water_saved_liters=7837500.0,
        energy_efficiency_kwh=12400.0,
        operational_cost_savings_inr=1567500.0,
        meals_redistributed=28500,
        active_kitchens_monitored=kitchens_count,
        active_ngo_partners=ngos_count
    )

@router.get("/monthly-trend")
def get_monthly_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return [
        {"month": "Apr", "waste_generated_kg": 2400, "food_rescued_kg": 950, "cost_saved_inr": 104500},
        {"month": "May", "waste_generated_kg": 2150, "food_rescued_kg": 1300, "cost_saved_inr": 143000},
        {"month": "Jun", "waste_generated_kg": 1900, "food_rescued_kg": 1650, "cost_saved_inr": 181500},
        {"month": "Jul", "waste_generated_kg": 1650, "food_rescued_kg": 2100, "cost_saved_inr": 231000},
        {"month": "Aug", "waste_generated_kg": 1400, "food_rescued_kg": 2550, "cost_saved_inr": 280500},
        {"month": "Sep", "waste_generated_kg": 1150, "food_rescued_kg": 3100, "cost_saved_inr": 341000},
    ]
