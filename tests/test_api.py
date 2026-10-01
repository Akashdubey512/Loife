import pytest
from datetime import datetime, date, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.core.database import Base, engine, SessionLocal
from backend.services.seed_service import seed_database
from backend.models.entities import (
    DemandPrediction,
    WastePrediction,
    Alert,
    QualityResult,
    RedistributionRequest,
    Route,
    Delivery,
    Inventory,
    InventoryBatch,
    User,
    Organization,
)
from backend.core.security import hash_password

# Ensure database tables and seeds exist before tests run
Base.metadata.create_all(bind=engine)
seed_database(force=True)

client = TestClient(app)

def get_auth_token(email: str = "admin@reserveai.com", password: str = "Admin@1234") -> str:
    response = client.post("/api/v1/auth/login", json={
        "username": email,
        "password": password
    })
    assert response.status_code == 200, f"Login failed for {email}: {response.text}"
    return response.json()["access_token"]

# 1. System Health & Executive Stats
def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"

def test_executive_stats():
    token = get_auth_token()
    response = client.get("/api/v1/analytics/executive-stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "total_food_saved_kg" in data
    assert data["waste_reduction_percentage"] >= 0

# 2. Authentication, Authorization & User Profile
def test_auth_login():
    response = client.post("/api/v1/auth/login", json={
        "username": "admin@reserveai.com",
        "password": "Admin@1234"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@reserveai.com"

def test_auth_me_endpoint():
    token = get_auth_token("kitchen@reserveai.com", "Kitchen@1234")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "kitchen@reserveai.com"
    assert user_data["role"] == "KITCHEN_MANAGER"

def test_auth_invalid_credentials():
    response = client.post("/api/v1/auth/login", json={
        "username": "admin@reserveai.com",
        "password": "WrongPassword!99"
    })
    assert response.status_code == 401

# 3. Workflow A: Demand Forecasting & Persistence
def test_demand_forecast():
    token = get_auth_token()
    response = client.get("/api/v1/demand/forecast?kitchen_id=1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) > 0
    assert data["predictions"][0]["expected_demand_kg"] > 0
    assert "recommended_production_kg" in data["predictions"][0]

def test_demand_prediction_persistence():
    token = get_auth_token()
    # Trigger forecast
    res = client.get("/api/v1/demand/forecast?kitchen_id=1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    
    # Verify persistence in database
    db: Session = SessionLocal()
    try:
        persisted = db.query(DemandPrediction).filter(DemandPrediction.kitchen_id == 1).all()
        assert len(persisted) > 0
        assert persisted[-1].expected_demand_kg > 0
        assert persisted[-1].model_version != ""
    finally:
        db.close()

# 4. Workflow B: Waste Prediction & Corrective Action
def test_waste_prediction():
    token = get_auth_token()
    response = client.get("/api/v1/waste/predictions?kitchen_id=1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "expected_waste_kg" in data
    assert "prevention_recommendation" in data
    assert 0.0 <= data["waste_probability"] <= 1.0

def test_waste_prediction_alert_generation():
    token = get_auth_token()
    # Query waste prediction which generates Alert when risk >= 20%
    res = client.get("/api/v1/waste/predictions?kitchen_id=1", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    
    db: Session = SessionLocal()
    try:
        alerts = db.query(Alert).filter(Alert.kitchen_id == 1).all()
        assert len(alerts) > 0
    finally:
        db.close()

# 5. Workflow C: Food Quality Assessment & Human Verification
def test_quality_scan_endpoint():
    token = get_auth_token("quality@reserveai.com", "Quality@1234")
    # Simulate multipart file upload
    file_payload = ("test_apple.jpg", b"mock-jpeg-image-bytes-spectral-test", "image/jpeg")
    response = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1, "category": "VEGETABLES", "food_name": "Test Honeycrisp Apple"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "freshness_score" in data
    assert data["freshness_level"] in ["FRESH", "MODERATE", "DEGRADING", "ROTTEN"]
    assert "sensor_safety_cleared" in data
    assert data["human_verified"] is False

def test_quality_human_verification_sign_off():
    token = get_auth_token("quality@reserveai.com", "Quality@1234")
    
    # 1. Create a scan
    file_payload = ("test_veggie.jpg", b"sample-bytes-for-verification", "image/jpeg")
    scan_res = client.post(
        "/api/v1/quality/scan",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": file_payload},
        data={"food_item_id": 1, "category": "VEGETABLES", "food_name": "Verified Farm Tomato"}
    )
    assert scan_res.status_code == 200
    scan_id = scan_res.json()["id"]

    # 2. Human inspector signs off
    verify_res = client.post(
        f"/api/v1/quality/scans/{scan_id}/verify",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "inspector_notes": "Sensory and physical check completed. Surface clean, no mold.",
            "final_disposition": "SAFE_FOR_REDISTRIBUTION",
            "override_model_decision": False
        }
    )
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["status"] == "SAFE_FOR_REDISTRIBUTION"
    assert v_data["food_safety_verdict"] == "APPROVED_FOR_REDISTRIBUTION"

# 6. Workflow D: Surplus Redistribution & Duplicate Prevention
def test_surplus_and_matching():
    token = get_auth_token()
    response = client.get("/api/v1/redistribution/surplus", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) > 0

def test_ngo_matching():
    token = get_auth_token()
    response = client.post("/api/v1/redistribution/match/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "recommended_matches" in data
    assert len(data["recommended_matches"]) > 0
    assert data["recommended_matches"][0]["compatibility_score"] > 0

def test_duplicate_redistribution_prevention():
    token = get_auth_token()
    db: Session = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        # Create a fresh unassigned surplus request for this test
        new_surplus = RedistributionRequest(
            kitchen_id=1,
            food_item_id=1,
            quantity_kg=25.0,
            estimated_meals=50,
            available_from=now_utc,
            expires_at=now_utc + timedelta(hours=6),
            status="POSTED"
        )
        db.add(new_surplus)
        db.commit()
        db.refresh(new_surplus)
        req_id = new_surplus.id
    finally:
        db.close()

    # 1. First claim must succeed
    first_claim = client.post(
        f"/api/v1/redistribution/requests/{req_id}/claim?ngo_id=2",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert first_claim.status_code == 200
    assert first_claim.json()["status"] in ["MATCHED", "SCHEDULED_FOR_PICKUP"]

    # 2. Second claim on same surplus must fail with 409 Conflict
    second_claim = client.post(
        f"/api/v1/redistribution/requests/{req_id}/claim?ngo_id=3",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert second_claim.status_code == 409
    detail_lower = second_claim.json()["detail"].lower()
    assert "already in" in detail_lower or "cannot be claimed" in detail_lower

# 7. Logistics, Routing & OTP Delivery Confirmation
def test_logistics_route_optimization_endpoint():
    token = get_auth_token("logistics@reserveai.com", "Logistics@1234")
    # First make sure requests are in MATCHED or SCHEDULED_FOR_PICKUP
    response = client.post(
        "/api/v1/logistics/routes/optimize",
        headers={"Authorization": f"Bearer {token}"},
        json={"kitchen_id": 1, "selected_requests": [1, 2], "vehicle_capacity_kg": 500.0}
    )
    assert response.status_code == 200
    route = response.json()
    assert "route_code" in route
    assert route["total_distance_km"] > 0
    assert len(route["waypoints"]) >= 2

def test_delivery_status_advance_and_pod_confirmation():
    token = get_auth_token("logistics@reserveai.com", "Logistics@1234")
    db: Session = SessionLocal()
    try:
        # Create a test delivery record with a known request and route
        test_delivery = Delivery(
            request_id=1,
            route_id=1,
            status="PENDING"
        )
        db.add(test_delivery)
        db.commit()
        db.refresh(test_delivery)
        del_id = test_delivery.id
    finally:
        db.close()

    # Confirm delivery with recipient signature, temperature, and OTP
    confirm_res = client.post(
        f"/api/v1/logistics/deliveries/{del_id}/confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "recipient_sign_name": "Sister Anita (Shelter Director)",
            "temperature_at_delivery": 3.6,
            "verification_otp": "4921",
            "proof_of_delivery_image": "/uploads/pod/sig_confirmed.png"
        }
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "DELIVERED"
    assert confirm_res.json()["recipient_sign_name"] == "Sister Anita (Shelter Director)"

# 8. Workflow E: Sustainability & ESG Audit Report
def test_sustainability_summary():
    token = get_auth_token()
    response = client.get("/api/v1/sustainability/summary", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "co2_avoided_kg" in data
    assert "water_saved_liters" in data
    assert "measured_verified_kg" in data

def test_sustainability_audit_report():
    token = get_auth_token()
    response = client.get(
        "/api/v1/sustainability/audit-report?organization_id=1&reporting_period=FY+2026-Q1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    report = response.json()
    assert report["scope_3_compliance_status"] == "AUDITED_AND_COMPLIANT_GHG_CAT_1"
    assert "co2e_avoided_kg" in report
    assert "equivalent_trees_planted" in report
    assert "car_km_emissions_offset" in report
    assert len(report["assumptions"]) > 0

# 9. IoT Sensor Ingestion & Threshold Alerts
def test_sensor_reading_normal():
    token = get_auth_token()
    response = client.post("/api/v1/sensors/readings", headers={"Authorization": f"Bearer {token}"}, json={
        "kitchen_id": 1,
        "sensor_id": "TEST-SENSOR-01",
        "sensor_type": "TEMPERATURE",
        "value": 3.4,
        "unit": "°C",
        "storage_zone": "Walk-in Cold Room A"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == "TEST-SENSOR-01"
    assert data["is_threshold_breached"] is False

def test_sensor_reading_threshold_breached():
    token = get_auth_token()
    response = client.post("/api/v1/sensors/readings", headers={"Authorization": f"Bearer {token}"}, json={
        "kitchen_id": 1,
        "sensor_id": "TEST-SENSOR-02",
        "sensor_type": "TEMPERATURE",
        "value": 14.8,  # Critical cold chain breach (> 8°C)
        "unit": "°C",
        "storage_zone": "Walk-in Cold Room A"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["is_threshold_breached"] is True

# 10. Multi-Tenant Isolation & Cross-Organization Security
def test_cross_tenant_access_denial():
    # Create User belonging to Organization 2
    db: Session = SessionLocal()
    try:
        org2 = db.query(Organization).filter(Organization.id == 2).first()
        if not org2:
            org2 = Organization(name="External NGO Cluster", org_type="NGO", contact_email="contact@ngo.org")
            db.add(org2)
            db.commit()
            db.refresh(org2)
        
        user_org2 = db.query(User).filter(User.email == "org2_user@example.com").first()
        if not user_org2:
            user_org2 = User(
                email="org2_user@example.com",
                hashed_password=hash_password("Pass@1234"),
                full_name="External Operator",
                role="ORG_ADMIN",
                organization_id=org2.id
            )
            db.add(user_org2)
            db.commit()
    finally:
        db.close()

    token_org2 = get_auth_token("org2_user@example.com", "Pass@1234")

    # Org 2 user attempts to access Org 1 sustainability audit report -> must receive 403 Forbidden
    forbidden_res = client.get(
        "/api/v1/sustainability/audit-report?organization_id=1",
        headers={"Authorization": f"Bearer {token_org2}"}
    )
    assert forbidden_res.status_code == 403
    assert "forbidden" in forbidden_res.json()["detail"].lower()

# 11. Core Engines Direct Unit Tests
def test_ml_demand_engine():
    from ml.demand_forecast import demand_engine
    result = demand_engine.predict(
        center_id=1,
        meal_id=1,
        target_date=date.today() + timedelta(days=1),
        base_price=120.0,
        checkout_price=110.0,
        historical_demands=[140.0, 145.0, 150.0, 148.0, 152.0, 155.0, 160.0]
    )
    assert result["expected_demand_kg"] > 0
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["engine_status"] == "ONLINE"

def test_ml_waste_engine():
    from ml.waste_predictor import waste_engine
    result = waste_engine.predict_waste(
        production_kg=150.0,
        expected_demand_kg=130.0,
        inventory_batches_near_expiry_kg=10.0
    )
    assert result["expected_waste_kg"] > 0
    assert "root_cause" in result
    assert result["model_version"] == "rule-based-v1.0"

def test_ml_sustainability_engine():
    from ml.sustainability_engine import sustainability_engine
    impact = sustainability_engine.calculate_impact(category="COOKED_MEALS", quantity_kg=100.0)
    assert impact["co2_avoided_kg"] == 250.0
    assert impact["water_saved_liters"] == 55000.0
    assert impact["financial_savings_inr"] == 11000.0

def test_cv_freshness_pipeline():
    from cv.freshness_classifier import FreshnessClassificationPipeline
    pipeline = FreshnessClassificationPipeline()
    dummy_bytes = b"fake-image-bytes-data-for-testing"
    res = pipeline.infer(dummy_bytes, food_name="Apples")
    assert res["freshness_level"] in ["FRESH", "MODERATE", "DEGRADING", "ROTTEN"]
    assert res["quality_score"] > 0
    assert "remaining_days" in res

def test_logistics_optimizer():
    from logistics.optimizer import VehicleRoutingOptimizer
    optimizer = VehicleRoutingOptimizer(vehicle_capacity_kg=500.0)
    depot = {"lat": 28.6139, "lng": 77.2090, "name": "Central Kitchen"}
    stops = [
        {"lat": 28.6200, "lng": 77.2150, "name": "Shelter A", "quantity_kg": 50, "urgency_hours": 2},
        {"lat": 28.6300, "lng": 77.2250, "name": "Food Bank B", "quantity_kg": 80, "urgency_hours": 5}
    ]
    route = optimizer.optimize_route(depot=depot, delivery_stops=stops)
    assert route["stops_count"] == 4
    assert route["total_distance_km"] > 0
    assert route["estimated_duration_min"] > 0
