from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.entities import Alert, User

router = APIRouter()

class AlertOut(BaseModel):
    id: int
    kitchen_id: int
    alert_type: str
    severity: str
    message: str
    is_resolved: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=List[AlertOut])
@router.get("/alerts", response_model=List[AlertOut])
def get_alerts(
    kitchen_id: int = 1,
    unresolved_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Alert)
    if kitchen_id:
        query = query.filter(Alert.kitchen_id == kitchen_id)
    if unresolved_only:
        query = query.filter(Alert.is_resolved == False)
    return query.order_by(Alert.created_at.desc()).limit(15).all()

@router.post("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.is_resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        db.commit()
    return {"message": "Alert resolved"}
