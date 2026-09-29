from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.security import verify_password, hash_password, create_access_token
from backend.core.config import settings
from backend.core.deps import get_current_user
from backend.core.rate_limiter import check_auth_rate_limit
from backend.models.entities import User
from backend.schemas.auth import Token, LoginRequest, UserCreate, UserOut

router = APIRouter()

@router.post("/login", response_model=Token)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(check_auth_rate_limit)
):
    user = db.query(User).filter(User.email == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }

SAFE_DEFAULT_ROLE = "PUBLIC_USER"

@router.post("/register", response_model=UserOut)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    _rate_limit: None = Depends(check_auth_rate_limit)
):
    if user_in.role and user_in.role.upper() != SAFE_DEFAULT_ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration cannot assign privileged roles."
        )
    if user_in.organization_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration cannot assign organization membership."
        )
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists."
        )
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=SAFE_DEFAULT_ROLE,
        organization_id=None,
        phone_number=user_in.phone_number
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/me", response_model=UserOut)
def get_authenticated_user_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated profile, role, and organization of the current user."""
    return current_user
