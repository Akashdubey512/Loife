from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.entities import ProductionBatch, User
from backend.schemas.demand import ProductionBatchCreate, ProductionBatchOut

router = APIRouter()

@router.get("/", response_model=List[ProductionBatchOut])
def list_production_batches(
    kitchen_id: int = 1,
    scheduled_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ProductionBatch).filter(ProductionBatch.kitchen_id == kitchen_id)
    if scheduled_date:
        query = query.filter(ProductionBatch.scheduled_for == scheduled_date)
    return query.order_by(ProductionBatch.scheduled_for.desc()).all()

@router.post("/", response_model=ProductionBatchOut)
def create_production_batch(
    batch_in: ProductionBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    batch = ProductionBatch(
        kitchen_id=batch_in.kitchen_id,
        food_item_id=batch_in.food_item_id,
        planned_quantity_kg=batch_in.planned_quantity_kg,
        meal_slot=batch_in.meal_slot,
        scheduled_for=batch_in.scheduled_for,
        status="SCHEDULED"
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch
