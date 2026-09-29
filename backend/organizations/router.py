from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.entities import Organization, User

router = APIRouter()

class OrganizationOut(BaseModel):
    id: int
    name: str
    org_type: str
    contact_email: str
    phone: Optional[str]
    address: Optional[str]
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=List[OrganizationOut])
def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Organization).all()
