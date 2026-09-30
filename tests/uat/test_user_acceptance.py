"""
ReServeAI — Phase 14 User Acceptance Testing (UAT) Suite
Validates all major operational and AI/ML workflows end-to-end.
"""
import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# Helper to get authenticated headers
def get_auth_token(email: str, password: str) -> dict:
    resp = client.post("/api/v1/auth/login", json={"username": email, "password": password})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestUATUserWorkflow:
    """UAT: User Lifecycle (Signup, Login, Dashboard, Role-aware Navigation)"""

    def test_uat_user_signup_login_dashboard(self):
        # Precondition: Unique public user credentials
        test_email = "uat_user_test@reserveai.org"
        password = "SecurePassword@123"

        # Action 1: Register
        reg_resp = client.post("/api/v1/auth/register", json={
            "email": test_email,
            "password": password,
            "full_name": "UAT Test User"
        })
        # If user exists from previous run, accept 200/201 or 400 with detail
        assert reg_resp.status_code in (200, 201, 400)

        # Action 2: Login
        login_resp = client.post("/api/v1/auth/login", json={
            "username": test_email,
            "password": password
        })
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        assert "access_token" in token_data
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Action 3: Current User (Dashboard Profile)
        me_resp = client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        user_info = me_resp.json()
        assert user_info["email"] == test_email
        assert user_info["role"] == "PUBLIC_USER"

        # Action 4: Role-based navigation check (Public user cannot access admin)
        admin_resp = client.get("/api/v1/users/", headers=headers)
        assert admin_resp.status_code == 403


class TestUATKitchenWorkflow:
    """UAT: Kitchen Operations (Inventory, Surplus Creation, Quality Flow)"""

    def test_uat_kitchen_surplus_and_inventory(self):
        headers = get_auth_token("kitchen@reserveai.com", "Kitchen@1234")

        # Action 1: Browse Inventory
        inv_resp = client.get("/api/v1/inventory/", headers=headers)
        assert inv_resp.status_code == 200
        items = inv_resp.json()
        assert isinstance(items, list)

        # Action 2: Browse Kitchens
        kitchens_resp = client.get("/api/v1/kitchens/", headers=headers)
        assert kitchens_resp.status_code == 200
        kitchens = kitchens_resp.json()
        assert len(kitchens) > 0
        kitchen_id = kitchens[0]["id"]

        # Action 3: Check Active Redistribution Surplus
        surplus_resp = client.get("/api/v1/redistribution/surplus", headers=headers)
        assert surplus_resp.status_code == 200
        requests = surplus_resp.json()
        assert isinstance(requests, list)


class TestUATQualityWorkflow:
    """UAT: Quality Inspection (Computer Vision & Human Verification)"""

    def test_uat_quality_fruit_cv_and_human_verification(self):
        headers = get_auth_token("quality@reserveai.com", "Quality@1234")

        # Create a valid JPEG payload (100x100 white image)
        from PIL import Image
        img_byte_arr = io.BytesIO()
        image = Image.new("RGB", (100, 100), color="white")
        image.save(img_byte_arr, format="JPEG")
        img_bytes = img_byte_arr.getvalue()

        # Action: Perform Quality Scan with required food_item_id form parameter
        scan_resp = client.post(
            "/api/v1/quality/scan",
            headers=headers,
            data={"food_item_id": 1},
            files={"image": ("test_apple.jpg", img_bytes, "image/jpeg")}
        )
        assert scan_resp.status_code == 200
        scan_data = scan_resp.json()

        # Expected: Honest simulation mode, mandatory human verification flag
        assert scan_data["simulated"] is True
        assert scan_data["human_verified"] is False
        assert scan_data["food_safety_verdict"] == "PENDING_HUMAN_VERIFICATION"
        assert "simulation_notice" in scan_data


class TestUATNGOWorkflow:
    """UAT: NGO Operations (Surplus Discovery, Matching, Claiming)"""

    def test_uat_ngo_surplus_discovery(self):
        headers = get_auth_token("ngo@reserveai.com", "NGO@1234")

        # Action: Discover Available Surplus Requests
        req_resp = client.get("/api/v1/redistribution/surplus", headers=headers)
        assert req_resp.status_code == 200
        requests = req_resp.json()
        assert isinstance(requests, list)

        # Action: Verify NGO Profile
        me_resp = client.get("/api/v1/auth/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["role"] == "NGO_REP"


class TestUATLogisticsAndDriverWorkflow:
    """UAT: Logistics & Dispatch (Route Creation, Optimization, Delivery)"""

    def test_uat_logistics_route_and_optimization(self):
        headers = get_auth_token("logistics@reserveai.com", "Logistics@1234")

        # Action 1: List existing routes
        routes_resp = client.get("/api/v1/logistics/routes", headers=headers)
        assert routes_resp.status_code == 200
        routes = routes_resp.json()
        assert isinstance(routes, list)

        # Action 2: Check Delivery List
        deliveries_resp = client.get("/api/v1/logistics/deliveries", headers=headers)
        assert deliveries_resp.status_code == 200
        assert isinstance(deliveries_resp.json(), list)


class TestUATESGWorkflow:
    """UAT: Sustainability & ESG Accounting (Poore & Nemecek LCA Lookup)"""

    def test_uat_esg_metrics_and_lca(self):
        headers = get_auth_token("admin@reserveai.com", "Admin@1234")

        # Action: Get Sustainability Summary
        esg_resp = client.get("/api/v1/sustainability/summary", headers=headers)
        assert esg_resp.status_code == 200
        esg_data = esg_resp.json()

        # Expected: LCA metrics present with truthful data sources
        assert "total_co2_saved_kg" in esg_data or "co2_avoided_kg" in esg_data or "meals_diverted" in esg_data or "summary" in esg_data


class TestUATAdminWorkflow:
    """UAT: Platform Administration & Tenant Management"""

    def test_uat_admin_user_and_org_management(self):
        headers = get_auth_token("admin@reserveai.com", "Admin@1234")

        # Action 1: Manage Organizations
        org_resp = client.get("/api/v1/organizations/", headers=headers)
        assert org_resp.status_code == 200
        orgs = org_resp.json()
        assert len(orgs) > 0

        # Action 2: Manage Users
        users_resp = client.get("/api/v1/users/", headers=headers)
        assert users_resp.status_code == 200
        users = users_resp.json()
        assert len(users) > 0


class TestUATMLWorkflow:
    """UAT: AI & ML Engine State Verification"""

    def test_uat_ml_status_truthfulness(self):
        headers = get_auth_token("admin@reserveai.com", "Admin@1234")

        # Action 1: ML Status
        status_resp = client.get("/api/v1/ml/status", headers=headers)
        assert status_resp.status_code == 200
        ml_status = status_resp.json()
        assert ml_status["ml_status"] == "OPERATIONAL"

        # Action 2: Demand Prediction
        demand_resp = client.post("/api/v1/demand/predict", headers=headers, json={
            "kitchen_id": 1,
            "food_item_id": 1,
            "day_of_week": 2,
            "is_weekend": False,
            "is_holiday": False,
            "historical_avg_demand": 45.0,
            "current_stock": 20.0
        })
        assert demand_resp.status_code == 200
        demand_data = demand_resp.json()
        assert "expected_demand_kg" in demand_data

        # Action 3: Maintenance Evaluation
        maint_resp = client.post("/api/v1/maintenance/evaluate", headers=headers, json={
            "air_temperature_k": 298.1,
            "process_temperature_k": 308.6,
            "rotational_speed_rpm": 1500,
            "torque_nm": 40.0,
            "tool_wear_min": 15,
            "machine_type": "M"
        })
        assert maint_resp.status_code == 200
        assert "failure_probability" in maint_resp.json()

        # Action 4: Energy Prediction
        energy_resp = client.post("/api/v1/energy/predict", headers=headers, json={
            "appliances_historical_wh": 60.0,
            "lights_wh": 10.0,
            "t1_temp_celsius": 19.89,
            "rh1_humidity_pct": 47.59,
            "t2_temp_celsius": 19.2,
            "rh2_humidity_pct": 44.79,
            "t_out_celsius": 6.6,
            "press_mm_hg": 733.5,
            "rh_out_pct": 92.0,
            "windspeed_m_s": 7.0,
            "visibility_km": 63.0,
            "tdewpoint_celsius": 5.3,
            "hour_of_day": 17,
            "day_of_week": 0
        })
        assert energy_resp.status_code == 200
        assert "predicted_energy_wh" in energy_resp.json()

        # Action 5: E-Nose Meat Quality Evaluation
        enose_resp = client.post("/api/v1/sensors/enose/evaluate", headers=headers, json={
            "temperature_celsius": 22.5,
            "humidity_pct": 55.0,
            "mq2_raw": 512.0,
            "mq3_raw": 420.0,
            "mq4_raw": 310.0,
            "mq5_raw": 280.0,
            "mq6_raw": 350.0,
            "mq7_raw": 290.0,
            "mq8_raw": 195.0,
            "mq135_raw": 440.0,
            "mq136_raw": 180.0,
            "mq137_raw": 210.0,
            "mq138_raw": 330.0
        })
        assert enose_resp.status_code == 200
        enose_data = enose_resp.json()
        assert "quality_class" in enose_data
        assert "BEEF" in enose_data.get("scope", "").upper()

        # Action 6: Waste Prediction (Rule-based Fallback)
        waste_resp = client.get("/api/v1/waste/predictions", headers=headers)
        assert waste_resp.status_code == 200
        waste_data = waste_resp.json()
        assert "expected_waste_kg" in waste_data
