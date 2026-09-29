from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.entities import SensorReading, Alert, User
from backend.schemas.sensors import SensorReadingCreate, SensorReadingOut

router = APIRouter()

# Thresholds
THRESHOLDS = {
    "TEMPERATURE": {"min": 0.0, "max": 7.0, "unit": "°C"},
    "HUMIDITY": {"min": 30.0, "max": 75.0, "unit": "%RH"},
    "GAS_METHANE": {"min": 0.0, "max": 25.0, "unit": "PPM"},
}

@router.get("/live", response_model=List[SensorReadingOut])
def get_live_sensors(
    kitchen_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch latest reading per sensor
    readings = db.query(SensorReading).filter(
        SensorReading.kitchen_id == kitchen_id
    ).order_by(SensorReading.timestamp.desc()).limit(12).all()
    return readings

@router.post("/readings", response_model=SensorReadingOut)
def record_sensor_reading(
    reading_in: SensorReadingCreate,
    db: Session = Depends(get_db)
):
    # Detect threshold breach
    is_breached = False
    thresh = THRESHOLDS.get(reading_in.sensor_type)
    if thresh:
        if reading_in.value < thresh["min"] or reading_in.value > thresh["max"]:
            is_breached = True

    reading = SensorReading(
        kitchen_id=reading_in.kitchen_id,
        sensor_id=reading_in.sensor_id,
        sensor_type=reading_in.sensor_type,
        value=reading_in.value,
        unit=reading_in.unit,
        storage_zone=reading_in.storage_zone,
        is_threshold_breached=is_breached,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(reading)

    if is_breached:
        alert = Alert(
            kitchen_id=reading_in.kitchen_id,
            alert_type="CRITICAL_STORAGE_BREACH",
            severity="CRITICAL",
            message=f"Storage alert in {reading_in.storage_zone}: {reading_in.sensor_type} reading of {reading_in.value}{reading_in.unit} breached safety limit!"
        )
        db.add(alert)

    db.commit()
    db.refresh(reading)
    return reading
