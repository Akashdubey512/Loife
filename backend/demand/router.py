from typing import List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user, check_tenant_access
from backend.models.entities import DemandPrediction, DemandHistory, Inventory, FoodItem, Kitchen, User
from backend.schemas.demand import (
    DemandForecastResponse, DemandForecastItem,
    DemandPredictRequest, DemandPredictResponse
)
from ml.demand_forecast import demand_engine

router = APIRouter()

@router.get("/forecast", response_model=DemandForecastResponse)
def get_demand_forecast(
    kitchen_id: int = Query(1, description="Kitchen facility identifier"),
    forecast_date: Optional[date] = Query(None, description="Target forecast date"),
    meal_slot: Optional[str] = Query("LUNCH", description="Meal slot: BREAKFAST, LUNCH, DINNER, SNACK"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Workflow A: Intelligent Food Demand Planning
    Historical consumption + calendar + inventory + kitchen data
    -> Demand forecasting model -> Predicted demand -> Recommended production quantity
    -> Inventory availability check -> Production recommendation -> Persist & Visualize.
    """
    kitchen = db.query(Kitchen).filter(Kitchen.id == kitchen_id).first()
    if not kitchen:
        raise HTTPException(status_code=404, detail="Kitchen facility not found")
    check_tenant_access(current_user, kitchen.organization_id)

    target_date = forecast_date or (datetime.now().date() + timedelta(days=1))

    # Check existing predictions in DB
    existing_preds = db.query(DemandPrediction).filter(
        DemandPrediction.kitchen_id == kitchen_id,
        DemandPrediction.prediction_date == target_date,
        DemandPrediction.meal_slot == meal_slot
    ).all()

    items_list = []
    if existing_preds:
        for p in existing_preds:
            food = db.query(FoodItem).filter(FoodItem.id == p.food_item_id).first()
            items_list.append(DemandForecastItem(
                food_item_id=p.food_item_id,
                food_name=food.name if food else f"Item #{p.food_item_id}",
                expected_demand_kg=p.expected_demand_kg,
                confidence_score=p.confidence_score,
                recommended_production_kg=p.recommended_production_kg,
                surplus_risk_probability=p.surplus_risk_probability,
                model_version=p.model_version
            ))
    else:
        # Generate fresh forecast using domain ML pipeline (LightGBM Genpact baseline)
        food_items = db.query(FoodItem).all()
        if not food_items:
            food_items = [
                FoodItem(id=1, name="Basmati Rice & Dal Makhani", category="COOKED_MEALS"),
                FoodItem(id=2, name="Paneer Butter Masala", category="COOKED_MEALS"),
                FoodItem(id=3, name="Mixed Green Salad", category="VEGETABLES"),
                FoodItem(id=4, name="Whole Wheat Roti / Naan", category="BAKERY"),
            ]

        for item in food_items[:6]:
            # 1. Fetch historical consumption from DemandHistory
            history_rows = db.query(DemandHistory).filter(
                DemandHistory.kitchen_id == kitchen_id,
                DemandHistory.food_item_id == item.id,
                DemandHistory.meal_slot == meal_slot
            ).order_by(DemandHistory.date.desc()).limit(7).all()

            if history_rows:
                hist_demands = [h.actual_consumption_kg for h in reversed(history_rows)]
            else:
                # Aligned with kitchen meal capacity
                base_val = (kitchen.daily_meal_capacity / 1500.0) * 145.0
                hist_demands = [base_val * 0.95, base_val * 1.02, base_val * 0.98, base_val * 1.05, base_val * 1.0, base_val * 1.08, base_val * 1.04]

            # 2. Run LightGBM ML demand engine
            ml_pred = demand_engine.predict(
                center_id=kitchen_id,
                meal_id=item.id,
                target_date=target_date,
                historical_demands=hist_demands
            )

            # 3. Inventory availability check: on-hand stock reduces raw production need
            inv = db.query(Inventory).filter(
                Inventory.kitchen_id == kitchen_id,
                Inventory.food_item_id == item.id
            ).first()
            usable_stock = inv.current_quantity_kg if inv else 0.0

            # Buffer production adjustment
            expected_demand = ml_pred["expected_demand_kg"]
            raw_rec = ml_pred["recommended_production_kg"]
            # Deduct up to 30% of existing stock to avoid stockout while preventing overprep
            recommended_prod = round(max(expected_demand * 0.85, raw_rec - (usable_stock * 0.25)), 1)

            # 4. Persist prediction record
            db_pred = DemandPrediction(
                kitchen_id=kitchen_id,
                food_item_id=item.id,
                prediction_date=target_date,
                meal_slot=meal_slot,
                expected_demand_kg=expected_demand,
                confidence_score=ml_pred["confidence"],
                recommended_production_kg=recommended_prod,
                surplus_risk_probability=ml_pred["surplus_probability"],
                model_version=f"{ml_pred['model_type']}-genpact-v1.4"
            )
            db.add(db_pred)

            items_list.append(DemandForecastItem(
                food_item_id=item.id,
                food_name=item.name,
                expected_demand_kg=expected_demand,
                confidence_score=ml_pred["confidence"],
                recommended_production_kg=recommended_prod,
                surplus_risk_probability=ml_pred["surplus_probability"],
                model_version=db_pred.model_version
            ))

        db.commit()

    return DemandForecastResponse(
        prediction_date=target_date,
        meal_slot=meal_slot,
        kitchen_id=kitchen_id,
        predictions=items_list
    )

@router.post("/predict", response_model=DemandPredictResponse)
def predict_demand(
    req: DemandPredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Workflow A: Intelligent Food Demand Planning (Interactive Endpoint)
    Calculates predicted meal demand, checks existing inventory on hand,
    subtracts available stock for net recommended prep, and persists prediction.
    """
    kitchen = db.query(Kitchen).filter(Kitchen.id == req.kitchen_id).first()
    if not kitchen:
        raise HTTPException(status_code=404, detail="Kitchen facility not found")
    check_tenant_access(current_user, kitchen.organization_id)

    target_date = req.prediction_date or (datetime.now().date() + timedelta(days=1))

    # 1. Query past consumption lags
    history = db.query(DemandHistory).filter(
        DemandHistory.kitchen_id == req.kitchen_id,
        DemandHistory.food_item_id == req.food_item_id
    ).order_by(DemandHistory.date.desc()).limit(7).all()
    lags = [h.actual_consumption_kg for h in history] if history else [175.0, 168.0, 182.0, 170.0, 174.0, 180.0, 169.0]

    # 2. Run LightGBM ML model
    pred_result = demand_engine.predict(
        center_id=req.kitchen_id,
        meal_id=req.food_item_id,
        target_date=target_date,
        past_consumption_lags=lags,
        footfall=req.expected_footfall or 450,
        is_holiday=False,
        is_weekend=target_date.weekday() >= 5,
        promotion_active=False
    )
    predicted_demand = pred_result["expected_demand_kg"]

    # 3. Inventory availability check (net production accounting)
    inv = db.query(Inventory).filter(
        Inventory.kitchen_id == req.kitchen_id,
        Inventory.food_item_id == req.food_item_id
    ).first()
    on_hand = inv.current_quantity_kg if inv else 0.0

    net_prep = max(0.0, round(predicted_demand - on_hand, 1))

    # 4. Food item name
    food = db.query(FoodItem).filter(FoodItem.id == req.food_item_id).first()
    food_name = food.name if food else f"Food Item #{req.food_item_id}"

    # 5. Persist prediction
    new_pred = DemandPrediction(
        kitchen_id=req.kitchen_id,
        food_item_id=req.food_item_id,
        prediction_date=target_date,
        meal_slot=req.meal_slot or "LUNCH",
        expected_demand_kg=predicted_demand,
        confidence_score=pred_result["confidence_score"],
        recommended_production_kg=net_prep,
        surplus_risk_probability=pred_result["surplus_risk_probability"],
        model_version=pred_result.get("model_version", "lgbm-genpact-v1.4")
    )
    db.add(new_pred)
    db.commit()
    db.refresh(new_pred)

    return DemandPredictResponse(
        id=new_pred.id,
        kitchen_id=new_pred.kitchen_id,
        food_item_id=new_pred.food_item_id,
        food_name=food_name,
        expected_demand_kg=predicted_demand,
        current_inventory_on_hand_kg=on_hand,
        net_recommended_production_kg=net_prep,
        recommended_production_kg=net_prep,
        surplus_risk_probability=pred_result["surplus_risk_probability"],
        confidence_score=pred_result["confidence_score"],
        model_version=pred_result.get("model_version", "lgbm-genpact-v1.4")
    )

