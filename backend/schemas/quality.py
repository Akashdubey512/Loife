from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class QualityScanResponse(BaseModel):
    id: int
    food_item_id: int
    food_name: str
    image_url: str
    freshness_score: float
    freshness_level: str
    remaining_shelf_life_days: float
    redistribution_status: str
    confidence: float
    inspected_at: datetime
    defects_detected: List[str] = []
    sensor_safety_cleared: bool = True
    human_verified: bool = False
    food_safety_verdict: str = "PENDING_HUMAN_VERIFICATION"
    model_config = ConfigDict(from_attributes=True)

class QualityResultOut(BaseModel):
    id: int
    batch_id: Optional[int]
    food_item_id: int
    image_url: str
    freshness_level: str
    freshness_score: float
    remaining_shelf_life_days: float
    redistribution_status: str
    confidence: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class QualityVerificationRequest(BaseModel):
    verdict: Optional[str] = "APPROVED_FOR_REDISTRIBUTION"
    final_disposition: Optional[str] = None
    inspector_notes: Optional[str] = "Visual inspection verified compliant with FSSAI regulations."
    override_model_decision: Optional[bool] = False

class QualityVerificationResponse(BaseModel):
    scan_id: int
    status: str
    food_safety_verdict: str
    verified_by_user_id: int
    inspector_name: Optional[str] = None
    verified_at: datetime
    notes: Optional[str] = None
    human_verified: bool = True
