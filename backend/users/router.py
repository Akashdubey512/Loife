from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user, require_roles
from backend.core.security import hash_password
from backend.models.entities import User
from backend.schemas.auth import UserOut, UserCreate

router = APIRouter()

@router.get("/me", response_model=UserOut)
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[UserOut])
def read_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORG_ADMIN"]))
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=UserOut)
def create_user_administrative(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "ORG_ADMIN"]))
):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists."
        )

    # ORG_ADMIN cannot create SUPER_ADMIN or assign to a different organization
    if current_user.role != "SUPER_ADMIN":
        if user_in.role == "SUPER_ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only SUPER_ADMIN can create administrator accounts."
            )
        target_org_id = current_user.organization_id
    else:
        target_org_id = user_in.organization_id

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role or "KITCHEN_STAFF",
        organization_id=target_org_id,
        phone_number=user_in.phone_number
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
