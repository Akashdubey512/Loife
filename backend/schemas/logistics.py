from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class Waypoint(BaseModel):
    lat: float
    lng: float
    name: str
    action: str  # PICKUP, DELIVERY
    demand_kg: float

class RouteOut(BaseModel):
    id: int
    route_code: str
    vehicle_id: str
    driver_name: str
    driver_phone: str
    total_distance_km: float
    estimated_duration_min: int
    waypoints: List[Dict[str, Any]] = []
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class RouteOptimizeRequest(BaseModel):
    kitchen_id: Optional[int] = 1
    selected_requests: Optional[List[int]] = None
    request_ids: Optional[List[int]] = None
    vehicle_capacity_kg: float = 500.0

class DeliveryConfirmRequest(BaseModel):
    recipient_sign_name: Optional[str] = "Authorized Recipient"
    temperature_at_delivery: float = 65.0
    verification_otp: str = "4921"
    proof_of_delivery_image: Optional[str] = "/uploads/pod/sig_confirmed.png"

class DeliveryOut(BaseModel):
    id: int
    route_id: int
    request_id: int
    stop_sequence: int
    pickup_time: Optional[datetime]
    delivered_time: Optional[datetime]
    temperature_at_delivery: Optional[float]
    recipient_sign_name: Optional[str]
    status: str
    model_config = ConfigDict(from_attributes=True)
