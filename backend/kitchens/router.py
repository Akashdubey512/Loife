from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.entities import Kitchen, ProductionBatch, RedistributionRequest, Alert, User
from backend.schemas.kitchens import KitchenOut, KitchenCreate, KitchenOverview

router = APIRouter()

@router.get("/", response_model=List[KitchenOut])
def list_kitchens(
    organization_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Kitchen)
    if organization_id:
        query = query.filter(Kitchen.organization_id == organization_id)
    return query.all()

@router.get("/{kitchen_id}/overview", response_model=KitchenOverview)
def get_kitchen_overview(
    kitchen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    kitchen = db.query(Kitchen).filter(Kitchen.id == kitchen_id).first()
    if not kitchen:
        raise HTTPException(status_code=404, detail="Kitchen not found")

    active_batches = db.query(ProductionBatch).filter(
        ProductionBatch.kitchen_id == kitchen_id,
        ProductionBatch.status.in_(["SCHEDULED", "IN_PREPARATION"])
    ).count()

    surplus_reqs = db.query(RedistributionRequest).filter(
        RedistributionRequest.kitchen_id == kitchen_id,
        RedistributionRequest.status == "POSTED"
    ).all()
    surplus_kg = sum(r.quantity_kg for r in surplus_reqs)

    pending_alerts = db.query(Alert).filter(
        Alert.kitchen_id == kitchen_id,
        Alert.is_resolved == False
    ).count()

    return KitchenOverview(
        kitchen_id=kitchen.id,
        kitchen_name=kitchen.name,
        daily_capacity=kitchen.daily_meal_capacity,
        active_batches_count=active_batches,
        surplus_available_kg=round(surplus_kg, 1),
        waste_diverted_kg_today=45.2,
        cold_chain_status="Optimal (2.8°C avg)",
        pending_alerts=pending_alerts
    )
