from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SensorReadingCreate(BaseModel):
    kitchen_id: int
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    storage_zone: str

class SensorReadingOut(SensorReadingCreate):
    id: int
    is_threshold_breached: bool
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class MachineHealthOut(BaseModel):
    machine_id: str
    machine_type: str
    failure_probability: float
    failure_type: str
    status: str
    recommended_action: str
