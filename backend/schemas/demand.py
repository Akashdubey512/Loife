from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

class DemandForecastItem(BaseModel):
    food_item_id: int
    food_name: str
    expected_demand_kg: float
    confidence_score: float
    recommended_production_kg: float
    surplus_risk_probability: float
    model_version: str = "lgbm-v1.4"

class DemandForecastResponse(BaseModel):
    prediction_date: date
    meal_slot: str
    kitchen_id: int
    predictions: List[DemandForecastItem]

class DemandPredictRequest(BaseModel):
    kitchen_id: int = 1
    food_item_id: int = 1
    prediction_date: Optional[date] = None
    meal_slot: Optional[str] = "LUNCH"
    expected_footfall: Optional[int] = 450

class DemandPredictResponse(BaseModel):
    id: int
    kitchen_id: int
    food_item_id: int
    food_name: str
    expected_demand_kg: float
    current_inventory_on_hand_kg: float
    net_recommended_production_kg: float
    recommended_production_kg: float
    surplus_risk_probability: float
    confidence_score: float
    model_version: str

class ProductionBatchCreate(BaseModel):
    kitchen_id: int
    food_item_id: int
    planned_quantity_kg: float
    meal_slot: str = "LUNCH"
    scheduled_for: date

class ProductionBatchOut(BaseModel):
    id: int
    kitchen_id: int
    food_item_id: int
    planned_quantity_kg: float
    actual_produced_kg: Optional[float] = None
    surplus_quantity_kg: float
    meal_slot: str
    scheduled_for: date
    status: str
    model_config = ConfigDict(from_attributes=True)
