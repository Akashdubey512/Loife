from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.entities import Inventory, InventoryBatch, FoodItem, User
from backend.schemas.inventory import InventoryOut, BatchCreate, InventoryBatchOut, FoodItemOut

router = APIRouter()

@router.get("/food-items", response_model=List[FoodItemOut])
def list_food_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(FoodItem).all()

@router.get("/", response_model=List[InventoryOut])
def get_inventory(
    kitchen_id: Optional[int] = 1,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Inventory).filter(Inventory.kitchen_id == kitchen_id)
    inventories = query.all()
    return inventories

@router.get("/batches/expiring", response_model=List[InventoryBatchOut])
def get_expiring_batches(
    kitchen_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    batches = db.query(InventoryBatch).join(Inventory).filter(
        Inventory.kitchen_id == kitchen_id,
        InventoryBatch.status.in_(["OPTIMAL", "NEARING_EXPIRY"])
    ).order_by(InventoryBatch.expiry_date.asc()).limit(10).all()
    return batches

@router.post("/batches", response_model=InventoryBatchOut)
def create_batch(
    batch_in: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    batch = InventoryBatch(
        inventory_id=batch_in.inventory_id,
        batch_number=batch_in.batch_number,
        initial_quantity_kg=batch_in.initial_quantity_kg,
        remaining_quantity_kg=batch_in.initial_quantity_kg,
        expiry_date=batch_in.expiry_date,
        status="OPTIMAL"
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch
