import sys
from pathlib import Path
from datetime import datetime, date, timedelta, timezone

# Ensure project root is in sys.path
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.core.database import SessionLocal, Base, engine
from backend.models.entities import (
    Organization, User, Kitchen, FoodItem, Inventory, InventoryBatch,
    DemandPrediction, SensorReading, NGOPartner, RedistributionRequest,
    Route, Delivery, Alert, MachineEvent, WasteEvent, SustainabilityMetric
)

def populate_rich_demo_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    now = datetime.now(timezone.utc)

    try:
        org = db.query(Organization).first()
        if not org:
            print("No organization found, aborting demo seed.")
            return

        kitchen1 = db.query(Kitchen).first()
        ngos = db.query(NGOPartner).all()
        food_items = db.query(FoodItem).all()

        if not kitchen1 or not ngos or not food_items:
            print("Base entities missing. Run seed_service first.")
            return

        # 1. Historical DELIVERED Redistribution Requests
        existing_delivered = db.query(RedistributionRequest).filter(RedistributionRequest.status == "DELIVERED").count()
        if existing_delivered < 4:
            historical_deliveries = [
                (food_items[0].id, ngos[0].id, 4200.0, 10500, now - timedelta(days=28)),
                (food_items[1].id, ngos[1].id, 3150.0, 7875, now - timedelta(days=21)),
                (food_items[2].id, ngos[0].id, 1850.0, 4625, now - timedelta(days=14)),
                (food_items[3].id, ngos[2].id, 2400.0, 6000, now - timedelta(days=7)),
                (food_items[4].id, ngos[1].id, 2650.0, 6625, now - timedelta(days=2)),
            ]
            for fi_id, ngo_id, kg, meals, dt in historical_deliveries:
                req = RedistributionRequest(
                    kitchen_id=kitchen1.id,
                    food_item_id=fi_id,
                    claimed_by_ngo_id=ngo_id,
                    quantity_kg=kg,
                    estimated_meals=meals,
                    available_from=dt - timedelta(hours=2),
                    expires_at=dt + timedelta(hours=4),
                    safe_temp_celsius=65.0,
                    status="DELIVERED",
                    created_at=dt - timedelta(hours=3)
                )
                db.add(req)
            db.commit()
            print(f"Added {len(historical_deliveries)} verified DELIVERED redistribution requests.")

        # 2. Historical SustainabilityMetrics
        existing_metrics = db.query(SustainabilityMetric).count()
        if existing_metrics < 6:
            monthly_data = [
                (date(2026, 4, 1), date(2026, 4, 30), 1850.0, 4625.0, 962000.0, 3700.0, 203500.0, 4625),
                (date(2026, 5, 1), date(2026, 5, 31), 2200.0, 5500.0, 1144000.0, 4400.0, 242000.0, 5500),
                (date(2026, 6, 1), date(2026, 6, 30), 2650.0, 6625.0, 1378000.0, 5300.0, 291500.0, 6625),
                (date(2026, 7, 1), date(2026, 7, 31), 3100.0, 7750.0, 1612000.0, 6200.0, 341000.0, 7750),
                (date(2026, 8, 1), date(2026, 8, 31), 3800.0, 9500.0, 1976000.0, 7600.0, 418000.0, 9500),
                (date(2026, 9, 1), date(2026, 9, 30), 4250.0, 10625.0, 2210000.0, 8500.0, 467500.0, 10625),
            ]
            for p_start, p_end, kg, co2, water, land, inr, meals in monthly_data:
                sm = SustainabilityMetric(
                    organization_id=org.id,
                    period_start=p_start,
                    period_end=p_end,
                    food_rescued_kg=kg,
                    co2_avoided_kg=co2,
                    water_saved_liters=water,
                    land_use_prevented_sqm=land,
                    cost_savings_inr=inr,
                    meals_served_to_needy=meals
                )
                db.add(sm)
            db.commit()
            print(f"Added {len(monthly_data)} historical SustainabilityMetric records.")

        # 3. Waste Events
        existing_waste = db.query(WasteEvent).count()
        if existing_waste < 5:
            waste_items = [
                (kitchen1.id, food_items[0].id, 12.5, "OVERPRODUCTION", "Unexpected rain decreased cafeteria attendance", 1375.0),
                (kitchen1.id, food_items[1].id, 8.0, "PLATE_LEFTOVER", "Buffet tray overfill at dinner service", 880.0),
                (kitchen1.id, food_items[2].id, 6.2, "STORAGE_EXPIRY", "Secondary walk-in sensor calibration delay", 682.0),
                (kitchen1.id, food_items[3].id, 4.5, "PREP_TRIMMING", "Trimming batch margin", 495.0),
            ]
            for k_id, fi_id, qty, stage, cause, loss in waste_items:
                we = WasteEvent(
                    kitchen_id=k_id,
                    food_item_id=fi_id,
                    quantity_wasted_kg=qty,
                    waste_stage=stage,
                    primary_cause=cause,
                    financial_loss_inr=loss,
                    logged_at=now - timedelta(days=1)
                )
                db.add(we)
            db.commit()
            print(f"Added {len(waste_items)} WasteEvent records.")

        # 4. Active Routes & Deliveries
        existing_route = db.query(Route).first()
        if not existing_route:
            rt = Route(
                route_code="RT-DELHI-NORTH-01",
                vehicle_id="EV-VAN-DL-4C-9921",
                driver_name="Rajesh Kumar",
                driver_phone="+91 98765 43210",
                total_distance_km=18.4,
                estimated_duration_min=45,
                status="IN_TRANSIT",
                started_at=now - timedelta(minutes=25)
            )
            db.add(rt)
            db.commit()
            db.refresh(rt)

            req = db.query(RedistributionRequest).filter(RedistributionRequest.status == "MATCHED").first()
            if req:
                deliv = Delivery(
                    route_id=rt.id,
                    request_id=req.id,
                    stop_sequence=1,
                    pickup_time=now - timedelta(minutes=20),
                    status="COLLECTED",
                    temperature_at_delivery=3.8,
                    recipient_sign_name="Kabir Singhania (Robin Hood Army)",
                    proof_of_delivery_image="/uploads/pod/sig_confirmed.png"
                )
                db.add(deliv)
                db.commit()
                print("Added active route and delivery.")

        print("Rich demo data successfully seeded into database.")

    finally:
        db.close()

if __name__ == "__main__":
    populate_rich_demo_data()
