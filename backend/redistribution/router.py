from typing import List, Optional
import math
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.entities import RedistributionRequest, NGOPartner, Kitchen, FoodItem, User
from backend.schemas.redistribution import (
    RedistributionRequestCreate, RedistributionRequestOut,
    NGOPartnerOut, MatchResponse, NGOMatchRecommendation
)

router = APIRouter()

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

@router.get("/surplus", response_model=List[RedistributionRequestOut])
def list_surplus(
    kitchen_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(RedistributionRequest)
    if kitchen_id:
        query = query.filter(RedistributionRequest.kitchen_id == kitchen_id)
    if status:
        query = query.filter(RedistributionRequest.status == status)

    requests = query.order_by(RedistributionRequest.created_at.desc()).all()
    results = []
    for r in requests:
        food = db.query(FoodItem).filter(FoodItem.id == r.food_item_id).first()
        ngo = db.query(NGOPartner).filter(NGOPartner.id == r.claimed_by_ngo_id).first() if r.claimed_by_ngo_id else None
        results.append(RedistributionRequestOut(
            id=r.id,
            kitchen_id=r.kitchen_id,
            food_item_id=r.food_item_id,
            food_item_name=food.name if food else f"Meal #{r.food_item_id}",
            claimed_by_ngo_id=r.claimed_by_ngo_id,
            claimed_by_ngo_name=ngo.name if ngo else None,
            quantity_kg=r.quantity_kg,
            estimated_meals=r.estimated_meals,
            available_from=r.available_from,
            expires_at=r.expires_at,
            safe_temp_celsius=r.safe_temp_celsius,
            status=r.status,
            created_at=r.created_at
        ))
    return results

@router.post("/surplus", response_model=RedistributionRequestOut)
def post_surplus(
    item_in: RedistributionRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = RedistributionRequest(
        kitchen_id=item_in.kitchen_id,
        food_item_id=item_in.food_item_id,
        quantity_kg=item_in.quantity_kg,
        estimated_meals=item_in.estimated_meals,
        expires_at=item_in.expires_at,
        safe_temp_celsius=item_in.safe_temp_celsius,
        status="POSTED"
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    food = db.query(FoodItem).filter(FoodItem.id == req.food_item_id).first()
    return RedistributionRequestOut(
        id=req.id,
        kitchen_id=req.kitchen_id,
        food_item_id=req.food_item_id,
        food_item_name=food.name if food else f"Meal #{req.food_item_id}",
        quantity_kg=req.quantity_kg,
        estimated_meals=req.estimated_meals,
        available_from=req.available_from,
        expires_at=req.expires_at,
        safe_temp_celsius=req.safe_temp_celsius,
        status=req.status,
        created_at=req.created_at
    )

@router.get("/ngos", response_model=List[NGOPartnerOut])
def list_ngos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(NGOPartner).all()

@router.post("/match/{request_id}", response_model=MatchResponse)
def match_surplus_with_ngos(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    surplus = db.query(RedistributionRequest).filter(RedistributionRequest.id == request_id).first()
    if not surplus:
        raise HTTPException(status_code=404, detail="Surplus request not found")

    kitchen = db.query(Kitchen).filter(Kitchen.id == surplus.kitchen_id).first()
    k_lat = kitchen.latitude if kitchen else 28.6139
    k_lng = kitchen.longitude if kitchen else 77.2090

    ngos = db.query(NGOPartner).all()
    recommendations = []

    for ngo in ngos:
        dist = haversine_distance(k_lat, k_lng, ngo.latitude, ngo.longitude)
        
        # Calculate matching compatibility score (0-100)
        # Factors: Distance penalty, Capacity sufficiency, Cold storage bonus, NGO Rating
        dist_score = max(0, 100 - (dist * 4.0))
        cap_score = min(100, (ngo.daily_meal_capacity / max(surplus.estimated_meals, 1)) * 50)
        rating_score = (ngo.rating / 5.0) * 100
        cold_chain_bonus = 10 if ngo.has_cold_storage else 0

        final_score = round((0.45 * dist_score) + (0.3 * cap_score) + (0.15 * rating_score) + (0.1 * cold_chain_bonus), 1)
        final_score = min(99.4, max(50.0, final_score))

        eta_min = int(10 + (dist * 3.2))

        recommendations.append(NGOMatchRecommendation(
            ngo_id=ngo.id,
            ngo_name=ngo.name,
            compatibility_score=final_score,
            distance_km=dist,
            capacity_available=ngo.daily_meal_capacity,
            has_cold_storage=ngo.has_cold_storage,
            eta_pickup_minutes=eta_min,
            address=ngo.address,
            phone=ngo.phone
        ))

    recommendations.sort(key=lambda x: x.compatibility_score, reverse=True)

    return MatchResponse(
        request_id=request_id,
        recommended_matches=recommendations[:5]
    )

@router.post("/claim/{request_id}")
@router.post("/requests/{request_id}/claim")
def claim_surplus(
    request_id: int,
    ngo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Claims/Pairs a surplus lot with an eligible NGO partner.
    Guarantees duplicate allocation prevention and verified partner status.
    """
    surplus = db.query(RedistributionRequest).filter(RedistributionRequest.id == request_id).with_for_update().first() if db.bind.dialect.name == "postgresql" else db.query(RedistributionRequest).filter(RedistributionRequest.id == request_id).first()
    if not surplus:
        raise HTTPException(status_code=404, detail="Surplus request not found")

    # Duplicate allocation prevention
    if surplus.status != "POSTED":
        raise HTTPException(
            status_code=409,
            detail=f"Surplus lot #{request_id} is already in '{surplus.status}' state and cannot be claimed again."
        )

    ngo = db.query(NGOPartner).filter(NGOPartner.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="Selected NGO partner not found")

    if ngo.verification_status != "VERIFIED":
        raise HTTPException(status_code=400, detail="Cannot assign surplus to unverified NGO partner")

    surplus.claimed_by_ngo_id = ngo_id
    surplus.status = "MATCHED"
    db.commit()
    db.refresh(surplus)
    return {
        "message": f"Surplus lot successfully paired with {ngo.name}",
        "request_id": surplus.id,
        "status": "MATCHED",
        "ngo_id": ngo.id,
        "ngo_name": ngo.name
    }

@router.post("/respond/{request_id}")
def respond_to_surplus_offer(
    request_id: int,
    accepted: bool,
    rejection_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """NGO partner confirms acceptance or rejection of matched surplus lot."""
    surplus = db.query(RedistributionRequest).filter(RedistributionRequest.id == request_id).first()
    if not surplus:
        raise HTTPException(status_code=404, detail="Surplus request not found")

    if surplus.status != "MATCHED":
        raise HTTPException(status_code=400, detail=f"Request status is '{surplus.status}'. Only MATCHED requests can be accepted or rejected.")

    if accepted:
        surplus.status = "SCHEDULED_FOR_PICKUP"
        msg = "Offer accepted by NGO partner. Ready for logistics fleet assignment."
    else:
        # Revert back to open pool for other NGOs
        surplus.status = "POSTED"
        surplus.claimed_by_ngo_id = None
        msg = f"Offer declined ({rejection_reason or 'Capacity constraint'}). Surplus lot returned to open pool."

    db.commit()
    return {"message": msg, "status": surplus.status}
