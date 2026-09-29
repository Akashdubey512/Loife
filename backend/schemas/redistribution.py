from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class NGOPartnerOut(BaseModel):
    id: int
    name: str
    contact_person: Optional[str]
    phone: str
    email: str
    address: str
    latitude: float
    longitude: float
    daily_meal_capacity: int
    has_cold_storage: bool
    rating: float
    model_config = ConfigDict(from_attributes=True)

class RedistributionRequestCreate(BaseModel):
    kitchen_id: int
    food_item_id: int
    quantity_kg: float
    estimated_meals: int
    expires_at: datetime
    safe_temp_celsius: Optional[float] = 65.0

class RedistributionRequestOut(BaseModel):
    id: int
    kitchen_id: int
    food_item_id: int
    food_item_name: Optional[str] = None
    claimed_by_ngo_id: Optional[int] = None
    claimed_by_ngo_name: Optional[str] = None
    quantity_kg: float
    estimated_meals: int
    available_from: datetime
    expires_at: datetime
    safe_temp_celsius: Optional[float]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class NGOMatchRecommendation(BaseModel):
    ngo_id: int
    ngo_name: str
    compatibility_score: float
    distance_km: float
    capacity_available: int
    has_cold_storage: bool
    eta_pickup_minutes: int
    address: str
    phone: str

class MatchResponse(BaseModel):
    request_id: int
    recommended_matches: List[NGOMatchRecommendation]
