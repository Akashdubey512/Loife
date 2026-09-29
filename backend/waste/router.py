from typing import List, Optional
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user, check_tenant_access
from backend.models.entities import (
    WasteEvent, WastePrediction, FoodItem, Kitchen, ProductionBatch,
    DemandPrediction, Inventory, InventoryBatch, Alert, User
)
from backend.schemas.waste import WasteEventCreate, WasteEventOut, WastePredictionOut
from ml.waste_predictor import waste_engine

router = APIRouter()

@router.get("/predictions", response_model=WastePredictionOut)
def get_waste_prediction(
    kitchen_id: int = Query(1, description="Kitchen facility identifier"),
    forecast_date: Optional[date] = Query(None, description="Forecast date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Workflow B: Food Waste Prevention
    Production data + inventory + historical waste -> Waste prediction
    -> Surplus risk detection -> Recommended corrective action -> Kitchen notification.
    """
    kitchen = db.query(Kitchen).filter(Kitchen.id == kitchen_id).first()
    if not kitchen:
        raise HTTPException(status_code=404, detail="Kitchen facility not found")
    check_tenant_access(current_user, kitchen.organization_id)

    target_date = forecast_date or datetime.now().date()
    existing = db.query(WastePrediction).filter(
        WastePrediction.kitchen_id == kitchen_id,
        WastePrediction.forecast_date == target_date
    ).first()

    if existing:
        return WastePredictionOut(
            kitchen_id=existing.kitchen_id,
            forecast_date=existing.forecast_date,
            expected_waste_kg=existing.expected_waste_kg,
            waste_probability=existing.waste_probability,
            predicted_root_cause=existing.predicted_root_cause,
            prevention_recommendation=existing.prevention_recommendation
        )

    # 1. Query production plans for the date
    prod_batches = db.query(ProductionBatch).filter(
        ProductionBatch.kitchen_id == kitchen_id,
        ProductionBatch.scheduled_for == target_date
    ).all()
    total_prod_kg = sum(b.planned_quantity_kg for b in prod_batches) or 165.0

    # 2. Query demand forecast for the date
    dem_preds = db.query(DemandPrediction).filter(
        DemandPrediction.kitchen_id == kitchen_id,
        DemandPrediction.prediction_date == target_date
    ).all()
    total_dem_kg = sum(d.expected_demand_kg for d in dem_preds) or (total_prod_kg * 0.90)

    # 3. Query inventory batches nearing expiry within 14 hours
    now = datetime.now(timezone.utc)
    expiry_horizon = now + timedelta(hours=14)
    expiring_batches = db.query(InventoryBatch).join(Inventory).filter(
        Inventory.kitchen_id == kitchen_id,
        InventoryBatch.expiry_date <= expiry_horizon,
        InventoryBatch.status.in_(["OPTIMAL", "NEARING_EXPIRY"])
    ).all()
    near_expiry_kg = sum(b.remaining_quantity_kg for b in expiring_batches) or 12.5

    # 4. Historical waste rate
    waste_history = db.query(WasteEvent).filter(WasteEvent.kitchen_id == kitchen_id).all()
    hist_rate = 0.06
    if waste_history:
        total_hist_waste = sum(w.quantity_wasted_kg for w in waste_history)
        hist_rate = round(min(0.20, max(0.03, total_hist_waste / max(total_prod_kg * 20, 1.0))), 3)

    # 5. Run XGBoost ML waste prediction engine
    ml_result = waste_engine.predict_waste(
        production_kg=total_prod_kg,
        expected_demand_kg=total_dem_kg,
        inventory_batches_near_expiry_kg=near_expiry_kg,
        historical_waste_rate=hist_rate
    )

    # 6. Persist prediction
    new_pred = WastePrediction(
        kitchen_id=kitchen_id,
        forecast_date=target_date,
        expected_waste_kg=ml_result["expected_waste_kg"],
        waste_probability=ml_result["waste_probability"],
        predicted_root_cause=ml_result["root_cause"],
        prevention_recommendation=ml_result["recommended_mitigation"]
    )
    db.add(new_pred)

    # 7. Generate kitchen notification alert if risk threshold is breached
    if ml_result["waste_probability"] >= 0.20 or ml_result["expected_waste_kg"] >= 15.0:
        existing_alert = db.query(Alert).filter(
            Alert.kitchen_id == kitchen_id,
            Alert.alert_type == "SURPLUS_SPOILED_RISK",
            Alert.is_resolved == False
        ).first()

        if not existing_alert:
            severity = "CRITICAL" if ml_result["waste_probability"] >= 0.50 else "WARNING"
            alert = Alert(
                kitchen_id=kitchen_id,
                alert_type="SURPLUS_SPOILED_RISK",
                severity=severity,
                message=f"Waste Risk Advisory ({int(ml_result['waste_probability']*100)}% prob): {ml_result['root_cause']}. Mitigation: {ml_result['recommended_mitigation']}"
            )
            db.add(alert)

    db.commit()
    db.refresh(new_pred)

    return WastePredictionOut(
        kitchen_id=new_pred.kitchen_id,
        forecast_date=new_pred.forecast_date,
        expected_waste_kg=new_pred.expected_waste_kg,
        waste_probability=new_pred.waste_probability,
        predicted_root_cause=new_pred.predicted_root_cause,
        prevention_recommendation=new_pred.prevention_recommendation
    )

@router.get("/events", response_model=List[WasteEventOut])
def list_waste_events(
    kitchen_id: int = Query(1, description="Kitchen facility identifier"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    kitchen = db.query(Kitchen).filter(Kitchen.id == kitchen_id).first()
    if kitchen:
        check_tenant_access(current_user, kitchen.organization_id)
    return db.query(WasteEvent).filter(WasteEvent.kitchen_id == kitchen_id).order_by(WasteEvent.logged_at.desc()).limit(limit).all()

@router.post("/events", response_model=WasteEventOut)
def log_waste_event(
    event_in: WasteEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Logs verified food waste, updates inventory/batch stock, and records financial loss."""
    if event_in.quantity_wasted_kg <= 0:
        raise HTTPException(status_code=400, detail="Wasted quantity must be greater than zero.")

    kitchen = db.query(Kitchen).filter(Kitchen.id == event_in.kitchen_id).first()
    if not kitchen:
        raise HTTPException(status_code=404, detail="Kitchen facility not found")
    check_tenant_access(current_user, kitchen.organization_id)

    # Auto-calculate financial loss if not supplied (Standard INR 110/kg meal rate)
    fin_loss = event_in.financial_loss_inr
    if fin_loss <= 0.0:
        fin_loss = round(event_in.quantity_wasted_kg * 110.0, 2)

    # Deduct from batch if applicable
    if event_in.batch_id:
        batch = db.query(InventoryBatch).filter(InventoryBatch.id == event_in.batch_id).first()
        if batch:
            batch.remaining_quantity_kg = max(0.0, batch.remaining_quantity_kg - event_in.quantity_wasted_kg)
            if batch.remaining_quantity_kg == 0.0:
                batch.status = "DEPLETED"

    event = WasteEvent(
        kitchen_id=event_in.kitchen_id,
        food_item_id=event_in.food_item_id,
        batch_id=event_in.batch_id,
        production_id=event_in.production_id,
        quantity_wasted_kg=event_in.quantity_wasted_kg,
        waste_stage=event_in.waste_stage,
        primary_cause=event_in.primary_cause,
        financial_loss_inr=fin_loss
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
