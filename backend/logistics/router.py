from typing import List, Optional, Dict, Any
import json
import random
import re
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.deps import get_current_user, check_tenant_access, require_roles
from backend.models.entities import (
    Route, Delivery, RedistributionRequest, Kitchen, NGOPartner,
    SustainabilityMetric, User, FoodItem
)
from backend.schemas.logistics import RouteOut, RouteOptimizeRequest, DeliveryConfirmRequest, DeliveryOut
from logistics.optimizer import logistics_optimizer

router = APIRouter()

@router.get("/routes", response_model=List[RouteOut])
def list_routes(
    status: Optional[str] = Query(None, description="Filter by route status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["LOGISTICS_COORDINATOR", "SUPER_ADMIN", "KITCHEN_MANAGER"]))
):
    query = db.query(Route)
    if status:
        query = query.filter(Route.status == status)

    routes = query.order_by(Route.id.desc()).all()
    results = []
    for r in routes:
        waypoints = []
        if r.waypoints_geojson:
            try:
                waypoints = json.loads(r.waypoints_geojson)
            except Exception:
                waypoints = []

        results.append(RouteOut(
            id=r.id,
            route_code=r.route_code,
            vehicle_id=r.vehicle_id,
            driver_name=r.driver_name,
            driver_phone=r.driver_phone,
            total_distance_km=r.total_distance_km,
            estimated_duration_min=r.estimated_duration_min,
            waypoints=waypoints,
            status=r.status,
            started_at=r.started_at,
            completed_at=r.completed_at
        ))
    return results

@router.post("/optimize", response_model=RouteOut)
@router.post("/routes/optimize", response_model=RouteOut)
def optimize_route(
    req: RouteOptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["LOGISTICS_COORDINATOR", "SUPER_ADMIN", "KITCHEN_MANAGER"]))
):
    """
    Workflow D: Dynamic Capacitated Vehicle Routing Problem (CVRPTW) Solver.
    Uses OR-Tools heuristic factoring vehicle capacity (default 500-600 kg),
    food remaining shelf-life urgency, and geographic coordinates.
    """
    kitchen = db.query(Kitchen).filter(Kitchen.id == req.kitchen_id).first()
    if not kitchen:
        raise HTTPException(status_code=404, detail="Kitchen facility not found")
    check_tenant_access(current_user, kitchen.organization_id)

    # 1. Fetch selected surplus lots
    target_ids = req.selected_requests or req.request_ids or []
    matched_requests = []
    if target_ids:
        matched_requests = db.query(RedistributionRequest).filter(
            RedistributionRequest.id.in_(target_ids),
            RedistributionRequest.kitchen_id == (req.kitchen_id or 1)
        ).all()

    if not matched_requests:
        # Fallback: grab any active MATCHED, POSTED, or SCHEDULED_FOR_PICKUP lots for this kitchen
        matched_requests = db.query(RedistributionRequest).filter(
            RedistributionRequest.kitchen_id == (req.kitchen_id or 1),
            RedistributionRequest.status.in_(["MATCHED", "SCHEDULED_FOR_PICKUP", "POSTED"])
        ).limit(4).all()

    if not matched_requests:
        raise HTTPException(
            status_code=400,
            detail="No eligible matched surplus lots found for vehicle route optimization. Please pair lots with NGOs first."
        )

    now_utc = datetime.now(timezone.utc)
    depot = {
        "name": f"{kitchen.name} (Central Hub)",
        "lat": kitchen.latitude,
        "lng": kitchen.longitude,
        "action": "PICKUP",
        "quantity_kg": 0.0
    }

    delivery_stops = []
    total_load = 0.0
    for s_req in matched_requests:
        ngo = db.query(NGOPartner).filter(NGOPartner.id == s_req.claimed_by_ngo_id).first() if s_req.claimed_by_ngo_id else None
        ngo_name = ngo.name if ngo else "Community Distribution Center"
        ngo_lat = ngo.latitude if ngo else (kitchen.latitude + 0.02)
        ngo_lng = ngo.longitude if ngo else (kitchen.longitude + 0.015)

        exp = s_req.expires_at.replace(tzinfo=timezone.utc) if (s_req.expires_at and s_req.expires_at.tzinfo is None) else s_req.expires_at
        urgency_hrs = max(1.0, (exp - now_utc).total_seconds() / 3600.0) if exp else 5.0
        delivery_stops.append({
            "request_id": s_req.id,
            "name": f"{ngo_name} (Lot #{s_req.id})",
            "action": "DELIVERY",
            "lat": ngo_lat,
            "lng": ngo_lng,
            "quantity_kg": s_req.quantity_kg,
            "urgency_hours": urgency_hrs
        })
        total_load += s_req.quantity_kg

    depot["quantity_kg"] = total_load

    # 2. Run OR-Tools vehicle routing optimization
    route_plan = logistics_optimizer.optimize_route(depot=depot, delivery_stops=delivery_stops)

    # 3. Format waypoints with sequence and status
    formatted_waypoints = []
    for idx, wp in enumerate(route_plan["optimized_waypoints"], start=1):
        load_change = wp.get("quantity_kg", 0.0) if wp.get("action") == "PICKUP" else -wp.get("quantity_kg", 0.0)
        formatted_waypoints.append({
            "sequence": idx,
            "name": wp.get("name", f"Stop #{idx}"),
            "action": wp.get("action", "DELIVERY"),
            "lat": wp.get("lat"),
            "lng": wp.get("lng"),
            "load_change_kg": load_change,
            "status": "COMPLETED" if idx == 1 else "PENDING",
            "request_id": wp.get("request_id")
        })

    # 4. Generate unique route code
    unique_suffix = random.randint(100, 999)
    route_code = f"RT-{kitchen.id}-{datetime.now().strftime('%m%d%H%M%S')}-{unique_suffix}"

    new_route = Route(
        route_code=route_code,
        vehicle_id="EV-VAN-DL-4C-9921",
        driver_name="Rajesh Kumar (Cold-Chain Certified)",
        driver_phone="+91 98765 43210",
        total_distance_km=route_plan["total_distance_km"],
        estimated_duration_min=route_plan["estimated_duration_min"],
        waypoints_geojson=json.dumps(formatted_waypoints),
        status="PLANNED",
        started_at=None
    )
    db.add(new_route)
    db.flush()

    # 5. Create Delivery records & advance request status to ASSIGNED_TO_ROUTE
    seq = 1
    for wp in formatted_waypoints:
        if wp.get("action") == "DELIVERY" and wp.get("request_id"):
            delivery = Delivery(
                route_id=new_route.id,
                request_id=wp["request_id"],
                stop_sequence=seq,
                pickup_time=now_utc,
                status="PENDING"
            )
            db.add(delivery)
            seq += 1

            req_obj = db.query(RedistributionRequest).filter(RedistributionRequest.id == wp["request_id"]).first()
            if req_obj:
                req_obj.status = "ASSIGNED_TO_ROUTE"

    db.commit()
    db.refresh(new_route)

    return RouteOut(
        id=new_route.id,
        route_code=new_route.route_code,
        vehicle_id=new_route.vehicle_id,
        driver_name=new_route.driver_name,
        driver_phone=new_route.driver_phone,
        total_distance_km=new_route.total_distance_km,
        estimated_duration_min=new_route.estimated_duration_min,
        waypoints=formatted_waypoints,
        status=new_route.status,
        started_at=new_route.started_at,
        completed_at=new_route.completed_at
    )

@router.post("/routes/{route_id}/advance", response_model=RouteOut)
def advance_route_status(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["LOGISTICS_COORDINATOR", "SUPER_ADMIN"]))
):
    """Advances route lifecycle: PLANNED -> IN_TRANSIT -> COMPLETED."""
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    now_utc = datetime.now(timezone.utc)
    if route.status == "PLANNED":
        route.status = "IN_TRANSIT"
        route.started_at = now_utc
        # Advance associated requests from ASSIGNED_TO_ROUTE to PICKED_UP
        deliveries = db.query(Delivery).filter(Delivery.route_id == route_id).all()
        for d in deliveries:
            if d.request and d.request.status == "ASSIGNED_TO_ROUTE":
                d.request.status = "PICKED_UP"
    elif route.status == "IN_TRANSIT":
        # Require all deliveries to be confirmed via OTP before completing the route
        pending_deliveries = db.query(Delivery).filter(
            Delivery.route_id == route_id,
            Delivery.status != "DELIVERED"
        ).all()
        if pending_deliveries:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot complete route #{route_id}: {len(pending_deliveries)} delivery stop(s) are still pending Proof of Delivery (OTP) confirmation."
            )
        route.status = "COMPLETED"
        route.completed_at = now_utc
    elif route.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Route has already been completed.")

    db.commit()
    db.refresh(route)

    waypoints = []
    if route.waypoints_geojson:
        try:
            waypoints = json.loads(route.waypoints_geojson)
        except Exception:
            waypoints = []

    return RouteOut(
        id=route.id,
        route_code=route_code if (route_code := route.route_code) else "",
        vehicle_id=route.vehicle_id,
        driver_name=route.driver_name,
        driver_phone=route.driver_phone,
        total_distance_km=route.total_distance_km,
        estimated_duration_min=route.estimated_duration_min,
        waypoints=waypoints,
        status=route.status,
        started_at=route.started_at,
        completed_at=route.completed_at
    )

@router.post("/deliveries/{delivery_id}/confirm", response_model=DeliveryOut)
def confirm_delivery(
    delivery_id: int,
    confirm_in: DeliveryConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["LOGISTICS_COORDINATOR", "SUPER_ADMIN", "NGO_REP"]))
):
    """
    Digital Proof of Delivery (PoD) with recipient signature, temperature validation, and OTP.
    Upon confirmation, marks food lot as verified rescued and updates ESG accounting records.
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery record not found")

    if delivery.status == "DELIVERED":
        raise HTTPException(status_code=400, detail="Delivery has already been confirmed.")

    otp = (confirm_in.verification_otp or "").strip()
    if not re.match(r"^\d{4,6}$", otp):
        raise HTTPException(
            status_code=400,
            detail="Invalid verification OTP: Must be a valid 4 to 6 digit numerical code."
        )

    if confirm_in.temperature_at_delivery is not None:
        if confirm_in.temperature_at_delivery < -25.0 or confirm_in.temperature_at_delivery > 100.0:
            raise HTTPException(
                status_code=400,
                detail="Invalid food temperature reading: Measured temperature must be within realistic cold-chain or hot-holding limits (-25°C to 100°C)."
            )

    now_utc = datetime.now(timezone.utc)
    delivery.status = "DELIVERED"
    delivery.delivered_time = now_utc
    delivery.recipient_sign_name = confirm_in.recipient_sign_name
    delivery.temperature_at_delivery = confirm_in.temperature_at_delivery
    delivery.proof_of_delivery_image = confirm_in.proof_of_delivery_image

    # If route is in PLANNED state, auto-advance to IN_TRANSIT
    if delivery.route and delivery.route.status == "PLANNED":
        delivery.route.status = "IN_TRANSIT"
        delivery.route.started_at = now_utc

    # Update associated RedistributionRequest
    s_req = db.query(RedistributionRequest).filter(RedistributionRequest.id == delivery.request_id).first()
    if s_req:
        s_req.status = "DELIVERED"

        # Update or create SustainabilityMetric entry
        kitchen = db.query(Kitchen).filter(Kitchen.id == s_req.kitchen_id).first()
        if kitchen:
            co2_factor = 2.5
            water_factor = 550.0
            land_factor = 2.0
            food_item = db.query(FoodItem).filter(FoodItem.id == s_req.food_item_id).first()
            if food_item:
                co2_factor = food_item.carbon_footprint_per_kg
                water_factor = food_item.water_footprint_per_kg

            today_date = now_utc.date()
            metric = db.query(SustainabilityMetric).filter(
                SustainabilityMetric.organization_id == kitchen.organization_id,
                SustainabilityMetric.period_start <= today_date,
                SustainabilityMetric.period_end >= today_date
            ).first()

            rescued_kg = s_req.quantity_kg
            if metric:
                metric.food_rescued_kg += rescued_kg
                metric.co2_avoided_kg += round(rescued_kg * co2_factor, 2)
                metric.water_saved_liters += round(rescued_kg * water_factor, 1)
                metric.land_use_prevented_sqm += round(rescued_kg * land_factor, 2)
                metric.cost_savings_inr += round(rescued_kg * 110.0, 2)
                metric.meals_served_to_needy += s_req.estimated_meals
            else:
                metric = SustainabilityMetric(
                    organization_id=kitchen.organization_id,
                    period_start=today_date.replace(day=1),
                    period_end=(today_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1),
                    food_rescued_kg=rescued_kg,
                    co2_avoided_kg=round(rescued_kg * co2_factor, 2),
                    water_saved_liters=round(rescued_kg * water_factor, 1),
                    land_use_prevented_sqm=round(rescued_kg * land_factor, 2),
                    cost_savings_inr=round(rescued_kg * 110.0, 2),
                    meals_served_to_needy=s_req.estimated_meals
                )
                db.add(metric)

    db.commit()
    db.refresh(delivery)
    return delivery

@router.get("/deliveries", response_model=List[DeliveryOut])
def list_deliveries(
    route_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Delivery)
    if route_id:
        query = query.filter(Delivery.route_id == route_id)
    if status:
        query = query.filter(Delivery.status == status)
    return query.order_by(Delivery.stop_sequence.asc()).all()
