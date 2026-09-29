from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.database import SessionLocal, Base, engine
from backend.core.security import hash_password
from backend.models.entities import (
    Organization, User, Kitchen, FoodItem, Inventory, InventoryBatch,
    DemandPrediction, SensorReading, NGOPartner, RedistributionRequest,
    Route, Alert, MachineEvent
)

def seed_database(force: bool = False):
    """
    Seeds initial realistic institutional fixtures and personas for development/demo.
    Strictly prohibited in production unless explicit non-production flag is provided.
    """
    env = getattr(settings, "ENVIRONMENT", "development").lower()
    if env == "production" and not force:
        raise RuntimeError(
            "Automatic or demo database seeding is strictly prohibited in production environment."
        )

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Organization
        org = db.query(Organization).first()
        if not org:
            org = Organization(
                name="Apex University Dining & Food Processing Cluster",
                org_type="UNIVERSITY",
                contact_email="campus.dining@apex.edu.in",
                phone="+91 11 2345 6789",
                address="Sector 62, Institutional Area, Delhi NCR",
                latitude=28.6280,
                longitude=77.3649,
                is_active=True
            )
            db.add(org)
            db.commit()
            db.refresh(org)

        # 2. Seed all 5 role personas (including standard and README aliases)
        demo_users_spec = [
            # Standard @reserveai.com suite
            ("admin@reserveai.com", "Admin@1234", "Dr. Vikram Malhotra (Sustainability Director)", "SUPER_ADMIN", "+91 98111 22334"),
            ("kitchen@reserveai.com", "Kitchen@1234", "Chef Priya Sharma (Executive Head Chef)", "KITCHEN_MANAGER", "+91 98111 22335"),
            ("quality@reserveai.com", "Quality@1234", "Aarav Mehta (Food Safety & QA Lead)", "QUALITY_INSPECTOR", "+91 98111 22336"),
            ("logistics@reserveai.com", "Logistics@1234", "Rohan Verma (Fleet Logistics Dispatcher)", "LOGISTICS_COORDINATOR", "+91 98111 22337"),
            ("ngo@reserveai.com", "NGO@1234", "Kabir Singhania (Robin Hood Army Rep)", "NGO_REP", "+91 98101 44552"),
            # README demo credential aliases
            ("admin@reserve.ai", "Admin@123", "Dr. Vikram Malhotra (Platform Admin)", "SUPER_ADMIN", "+91 98111 22334"),
            ("kitchen.lead@techcorp.com", "Kitchen@123", "Chef Priya Sharma (Kitchen Lead)", "KITCHEN_MANAGER", "+91 98111 22335"),
            ("inspector@reserve.ai", "Quality@123", "Aarav Mehta (Safety Inspector)", "QUALITY_INSPECTOR", "+91 98111 22336"),
            ("logistics@reserve.ai", "Logistics@123", "Rohan Verma (Dispatch Coordinator)", "LOGISTICS_COORDINATOR", "+91 98111 22337"),
            ("contact@robinhoodarmy.com", "NGO@123", "Kabir Singhania (NGO Representative)", "NGO_REP", "+91 98101 44552"),
        ]

        for email, pwd, name, role, phone in demo_users_spec:
            existing_user = db.query(User).filter(User.email == email).first()
            if not existing_user:
                u = User(
                    email=email,
                    hashed_password=hash_password(pwd),
                    full_name=name,
                    role=role,
                    organization_id=org.id,
                    phone_number=phone,
                    is_active=True
                )
                db.add(u)
        db.commit()

        # Check if rest of entities already seeded
        if db.query(Kitchen).first():
            # Ensure at least one POSTED surplus lot exists for demonstration
            posted = db.query(RedistributionRequest).filter(RedistributionRequest.status == "POSTED").first()
            if not posted:
                fi = db.query(FoodItem).first()
                k = db.query(Kitchen).first()
                if fi and k:
                    now = datetime.now(timezone.utc)
                    new_req = RedistributionRequest(
                        kitchen_id=k.id,
                        food_item_id=fi.id,
                        claimed_by_ngo_id=None,
                        quantity_kg=35.0,
                        estimated_meals=85,
                        available_from=now,
                        expires_at=now + timedelta(hours=6),
                        safe_temp_celsius=65.0,
                        status="POSTED"
                    )
                    db.add(new_req)
                    db.commit()
            return

        # 3. Kitchens
        kitchen1 = Kitchen(
            organization_id=org.id,
            name="Central Commissary & Mess Hall Alpha",
            facility_code="KIT-DELHI-001",
            daily_meal_capacity=2800,
            kitchen_type="COMMISSARY",
            latitude=28.6280,
            longitude=77.3649
        )
        kitchen2 = Kitchen(
            organization_id=org.id,
            name="South Wing Bakery & Processing Facility",
            facility_code="KIT-DELHI-002",
            daily_meal_capacity=1200,
            kitchen_type="PROCESSING_UNIT",
            latitude=28.6190,
            longitude=77.3580
        )
        db.add_all([kitchen1, kitchen2])
        db.commit()
        db.refresh(kitchen1)
        db.refresh(kitchen2)

        # 4. Food Items
        food_items = [
            FoodItem(name="Basmati Rice & Dal Makhani", category="COOKED_MEALS", perishable_type="HIGHLY_PERISHABLE", default_shelf_life_hours=12, carbon_footprint_per_kg=2.4, water_footprint_per_kg=520.0),
            FoodItem(name="Paneer Butter Masala", category="COOKED_MEALS", perishable_type="HIGHLY_PERISHABLE", default_shelf_life_hours=14, carbon_footprint_per_kg=3.8, water_footprint_per_kg=780.0),
            FoodItem(name="Farm Fresh Tomatoes & Bell Peppers", category="VEGETABLES", perishable_type="SEMI_PERISHABLE", default_shelf_life_hours=120, carbon_footprint_per_kg=0.5, water_footprint_per_kg=320.0),
            FoodItem(name="Fresh Dairy Paneer (Raw)", category="DAIRY", perishable_type="HIGHLY_PERISHABLE", default_shelf_life_hours=48, carbon_footprint_per_kg=4.2, water_footprint_per_kg=920.0),
            FoodItem(name="Multigrain Sandwich Bread & Buns", category="BAKERY", perishable_type="SEMI_PERISHABLE", default_shelf_life_hours=72, carbon_footprint_per_kg=1.5, water_footprint_per_kg=480.0),
            FoodItem(name="Seasonal Mixed Fruit Salad", category="FRUITS", perishable_type="HIGHLY_PERISHABLE", default_shelf_life_hours=24, carbon_footprint_per_kg=0.7, water_footprint_per_kg=280.0),
        ]
        db.add_all(food_items)
        db.commit()

        # 5. Inventory & Batches
        now = datetime.now(timezone.utc)
        for i, item in enumerate(food_items):
            inv = Inventory(
                kitchen_id=kitchen1.id,
                food_item_id=item.id,
                current_quantity_kg=85.0 + (i * 20.0),
                reorder_threshold_kg=20.0,
                storage_location=f"Zone {chr(65+i)} Cold Shelf {i+1}",
                last_audited_at=now
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)

            # Add batch
            batch = InventoryBatch(
                inventory_id=inv.id,
                batch_number=f"BATCH-{2026}-K1-{i+101}",
                initial_quantity_kg=inv.current_quantity_kg,
                remaining_quantity_kg=inv.current_quantity_kg,
                procured_at=now - timedelta(days=1),
                expiry_date=now + timedelta(hours=item.default_shelf_life_hours),
                status="OPTIMAL" if i > 1 else "NEARING_EXPIRY"
            )
            db.add(batch)
        db.commit()

        # 6. Demand Predictions
        tomorrow = (now + timedelta(days=1)).date()
        for item in food_items[:4]:
            pred = DemandPrediction(
                kitchen_id=kitchen1.id,
                food_item_id=item.id,
                prediction_date=tomorrow,
                meal_slot="LUNCH",
                expected_demand_kg=165.0,
                confidence_score=0.94,
                recommended_production_kg=175.0,
                surplus_risk_probability=0.07,
                model_version="lgbm-genpact-v1.4"
            )
            db.add(pred)
        db.commit()

        # 7. NGO Partners
        ngos = [
            NGOPartner(
                name="Robin Hood Army - Delhi Central Chapter",
                registration_number="NGO-DL-2018-9921",
                contact_person="Kabir Singhania",
                phone="+91 98101 44552",
                email="delhi@robinhoodarmy.com",
                address="Near Connaught Place Community Hall, New Delhi",
                latitude=28.6304,
                longitude=77.2177,
                daily_meal_capacity=850,
                has_cold_storage=True,
                verification_status="VERIFIED",
                rating=4.9
            ),
            NGOPartner(
                name="Feeding India by Zomato - Hub East",
                registration_number="NGO-DL-2020-4102",
                contact_person="Neha Gupta",
                phone="+91 98112 55663",
                email="east.delhi@feedingindia.org",
                address="Mayur Vihar Phase 1 Shelter Complex, New Delhi",
                latitude=28.6080,
                longitude=77.2950,
                daily_meal_capacity=600,
                has_cold_storage=True,
                verification_status="VERIFIED",
                rating=4.8
            ),
            NGOPartner(
                name="Roti Bank Foundation - Noida Sector 18",
                registration_number="NGO-UP-2019-3312",
                contact_person="Manoj Pandey",
                phone="+91 98113 66774",
                email="contact@rotibanknoida.org",
                address="Atta Market Relief Shelter, Noida",
                latitude=28.5700,
                longitude=77.3200,
                daily_meal_capacity=450,
                has_cold_storage=False,
                verification_status="VERIFIED",
                rating=4.7
            )
        ]
        db.add_all(ngos)
        db.commit()
        db.refresh(ngos[0])
        db.refresh(ngos[1])

        # 8. Redistribution Requests
        req1 = RedistributionRequest(
            kitchen_id=kitchen1.id,
            food_item_id=food_items[0].id,
            claimed_by_ngo_id=ngos[0].id,
            quantity_kg=48.0,
            estimated_meals=120,
            available_from=now,
            expires_at=now + timedelta(hours=5),
            safe_temp_celsius=65.0,
            status="MATCHED"
        )
        req2 = RedistributionRequest(
            kitchen_id=kitchen1.id,
            food_item_id=food_items[1].id,
            claimed_by_ngo_id=None,
            quantity_kg=35.0,
            estimated_meals=85,
            available_from=now,
            expires_at=now + timedelta(hours=6),
            safe_temp_celsius=65.0,
            status="POSTED"
        )
        db.add_all([req1, req2])
        db.commit()

        # 9. Sensors
        sensors_seed = [
            SensorReading(kitchen_id=kitchen1.id, sensor_id="SENS-TEMP-01", sensor_type="TEMPERATURE", value=3.2, unit="°C", storage_zone="Walk-in Cold Room A", is_threshold_breached=False),
            SensorReading(kitchen_id=kitchen1.id, sensor_id="SENS-HUM-01", sensor_type="HUMIDITY", value=62.0, unit="%RH", storage_zone="Walk-in Cold Room A", is_threshold_breached=False),
            SensorReading(kitchen_id=kitchen1.id, sensor_id="SENS-GAS-01", sensor_type="GAS_METHANE", value=4.5, unit="PPM", storage_zone="Cold Storage Exhaust", is_threshold_breached=False),
            SensorReading(kitchen_id=kitchen1.id, sensor_id="SENS-TEMP-02", sensor_type="TEMPERATURE", value=4.1, unit="°C", storage_zone="Dairy Chiller Room", is_threshold_breached=False),
        ]
        db.add_all(sensors_seed)

        # 10. Predictive Maintenance Machines
        machines_seed = [
            MachineEvent(kitchen_id=kitchen1.id, machine_id="CHILLER-01", machine_type="BLAST_CHILLER", failure_probability=0.03, status="HEALTHY"),
            MachineEvent(kitchen_id=kitchen1.id, machine_id="OVEN-02", machine_type="CONVECTION_OVEN", failure_probability=0.12, status="HEALTHY"),
            MachineEvent(kitchen_id=kitchen1.id, machine_id="COMPRESSOR-01", machine_type="REFRIGERATION_COMPRESSOR", failure_probability=0.05, status="HEALTHY")
        ]
        db.add_all(machines_seed)

        # 11. Sample Alerts
        alert1 = Alert(
            kitchen_id=kitchen1.id,
            alert_type="SURPLUS_SPOILED_RISK",
            severity="WARNING",
            message="48kg of Steamed Basmati Rice & Dal Makhani is ready for pickup. NGO dispatch en route (ETA 25m).",
            is_resolved=False
        )
        db.add(alert1)
        db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    print("Initiating explicit development database seeding...")
    seed_database(force=True)
    print("Development database seeding completed successfully.")
