from datetime import datetime
from pydantic import BaseModel, ConfigDict

class KitchenBase(BaseModel):
    name: str
    facility_code: str
    daily_meal_capacity: int = 1500
    kitchen_type: str = "MESS_HALL"
    latitude: float = 28.6139
    longitude: float = 77.2090

class KitchenCreate(KitchenBase):
    organization_id: int

class KitchenOut(KitchenBase):
    id: int
    organization_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class KitchenOverview(BaseModel):
    kitchen_id: int
    kitchen_name: str
    daily_capacity: int
    active_batches_count: int
    surplus_available_kg: float
    waste_diverted_kg_today: float
    cold_chain_status: str
    pending_alerts: int
