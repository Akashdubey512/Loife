from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class FoodItemOut(BaseModel):
    id: int
    name: str
    category: str
    perishable_type: str
    default_shelf_life_hours: int
    carbon_footprint_per_kg: float
    water_footprint_per_kg: float
    model_config = ConfigDict(from_attributes=True)

class InventoryBatchOut(BaseModel):
    id: int
    batch_number: str
    initial_quantity_kg: float
    remaining_quantity_kg: float
    procured_at: datetime
    expiry_date: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)

class InventoryOut(BaseModel):
    id: int
    kitchen_id: int
    food_item_id: int
    food_item: FoodItemOut
    current_quantity_kg: float
    reorder_threshold_kg: float
    storage_location: str
    last_audited_at: Optional[datetime]
    batches: List[InventoryBatchOut] = []
    model_config = ConfigDict(from_attributes=True)

class BatchCreate(BaseModel):
    inventory_id: int
    batch_number: str
    initial_quantity_kg: float
    expiry_date: datetime
