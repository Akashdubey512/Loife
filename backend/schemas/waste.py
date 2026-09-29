from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

class WastePredictionOut(BaseModel):
    kitchen_id: int
    forecast_date: date
    expected_waste_kg: float
    waste_probability: float
    predicted_root_cause: str
    prevention_recommendation: str

class WasteEventCreate(BaseModel):
    kitchen_id: int
    food_item_id: int
    batch_id: Optional[int] = None
    production_id: Optional[int] = None
    quantity_wasted_kg: float
    waste_stage: str
    primary_cause: str
    financial_loss_inr: float = 0.0

class WasteEventOut(WasteEventCreate):
    id: int
    logged_at: datetime
    model_config = ConfigDict(from_attributes=True)
