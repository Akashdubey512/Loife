import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from backend.main import app
from backend.core.database import SessionLocal
from backend.models.entities import (
    User, Kitchen, FoodItem, RedistributionRequest, Route, Delivery, SustainabilityMetric, NGOPartner
)

client = TestClient(app)

def get_auth_token(username: str, role: str) -> str:
    # Use standard test accounts
    passwords = {
        "admin@reserveai.com": "Admin@1234",
        "kitchen@reserveai.com": "Kitchen@1234",
        "quality@reserveai.com": "Quality@1234",
        "logistics@reserveai.com": "Logistics@1234",
        "ngo@reserveai.com": "NGO@1234",
    }
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": passwords[username]})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]


# =====================================================================
# DEFECT 1 & 5: Surplus Creation and Response Contract Reconciliation
# =====================================================================

def test_surplus_creation_canonical_and_alias():
    token = get_auth_token("kitchen@reserveai.com", "KITCHEN_MANAGER")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "kitchen_id": 1,
        "food_item_id": 1,
        "quantity_kg": 25.0,
        "estimated_meals": 60,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(),
        "safe_temp_celsius": 65.0
    }

    # 1. Canonical route: POST /redistribution/surplus
    res_canonical = client.post("/api/v1/redistribution/surplus", headers=headers, json=payload)
    assert res_canonical.status_code == 200, res_canonical.text
    data_c = res_canonical.json()
    assert data_c["status"] == "POSTED"
    assert data_c["quantity_kg"] == 25.0

    # 2. Alias route: POST /redistribution/requests
    res_alias = client.post("/api/v1/redistribution/requests", headers=headers, json=payload)
    assert res_alias.status_code == 200, res_alias.text
    data_a = res_alias.json()
    assert data_a["status"] == "POSTED"
    assert data_a["quantity_kg"] == 25.0


def test_surplus_respond_payload_and_alias():
    km_token = get_auth_token("kitchen@reserveai.com", "KITCHEN_MANAGER")
    ngo_token = get_auth_token("ngo@reserveai.com", "NGO_REP")
    km_headers = {"Authorization": f"Bearer {km_token}"}
    ngo_headers = {"Authorization": f"Bearer {ngo_token}"}

    # Step 1: Create a fresh surplus lot
    res_create = client.post("/api/v1/redistribution/surplus", headers=km_headers, json={
        "kitchen_id": 1,
        "food_item_id": 1,
        "quantity_kg": 20.0,
        "estimated_meals": 50,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
        "safe_temp_celsius": 65.0
    })
    assert res_create.status_code == 200
    lot_id = res_create.json()["id"]

    # Step 2: Claim surplus to transition to MATCHED
    res_claim = client.post(f"/api/v1/redistribution/requests/{lot_id}/claim?ngo_id=1", headers=ngo_headers)
    assert res_claim.status_code == 200
    assert res_claim.json()["status"] == "MATCHED"

    # Step 3: Test responding via frontend path with JSON body (ACCEPT)
    res_accept = client.post(f"/api/v1/redistribution/requests/{lot_id}/respond", headers=ngo_headers, json={
        "accept": True
    })
    assert res_accept.status_code == 200, res_accept.text
    assert res_accept.json()["status"] == "SCHEDULED_FOR_PICKUP"

    # Step 4: Create a second lot to test DECLINE / REJECTION workflow
    res_create2 = client.post("/api/v1/redistribution/surplus", headers=km_headers, json={
        "kitchen_id": 1,
        "food_item_id": 2,
        "quantity_kg": 15.0,
        "estimated_meals": 35,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
        "safe_temp_celsius": 65.0
    })
    assert res_create2.status_code == 200
    lot_id2 = res_create2.json()["id"]

    # Claim second lot
    client.post(f"/api/v1/redistribution/requests/{lot_id2}/claim?ngo_id=1", headers=ngo_headers)

    # Test declining with reason
    res_decline = client.post(f"/api/v1/redistribution/requests/{lot_id2}/respond", headers=ngo_headers, json={
        "accept": False,
        "rejection_reason": "Cold chain transport vehicle unavailable"
    })
    assert res_decline.status_code == 200, res_decline.text
    assert res_decline.json()["status"] == "POSTED"
    assert "returned to open pool" in res_decline.json()["message"]

    # Step 5: Test validation - missing accept field returns 422
    res_invalid = client.post(f"/api/v1/redistribution/requests/{lot_id2}/respond", headers=ngo_headers, json={
        "rejection_reason": "No accept flag provided"
    })
    assert res_invalid.status_code == 422


# =====================================================================
# DEFECT 2: Logistics Lifecycle and Proof-of-Delivery Integrity
# =====================================================================

def test_logistics_route_lifecycle_and_otp_validation():
    km_token = get_auth_token("kitchen@reserveai.com", "KITCHEN_MANAGER")
    ngo_token = get_auth_token("ngo@reserveai.com", "NGO_REP")
    log_token = get_auth_token("logistics@reserveai.com", "LOGISTICS_COORDINATOR")
    km_headers = {"Authorization": f"Bearer {km_token}"}
    ngo_headers = {"Authorization": f"Bearer {ngo_token}"}
    log_headers = {"Authorization": f"Bearer {log_token}"}

    # 1. Post surplus and match/schedule
    res_lot = client.post("/api/v1/redistribution/surplus", headers=km_headers, json={
        "kitchen_id": 1,
        "food_item_id": 1,
        "quantity_kg": 35.0,
        "estimated_meals": 90,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat(),
        "safe_temp_celsius": 65.0
    })
    lot_id = res_lot.json()["id"]
    client.post(f"/api/v1/redistribution/requests/{lot_id}/claim?ngo_id=1", headers=ngo_headers)
    client.post(f"/api/v1/redistribution/requests/{lot_id}/respond", headers=ngo_headers, json={"accept": True})

    # 2. Plan route via OR-Tools
    res_opt = client.post("/api/v1/logistics/routes/optimize", headers=log_headers, json={
        "kitchen_id": 1,
        "selected_requests": [lot_id],
        "vehicle_capacity_kg": 600.0
    })
    assert res_opt.status_code == 200
    route = res_opt.json()
    route_id = route["id"]

    # VERIFY LIFECYCLE RULE 1: Route starts in PLANNED status
    assert route["status"] == "PLANNED", f"Expected PLANNED initial status, got {route['status']}"
    assert route["started_at"] is None

    # 3. Advance route from PLANNED to IN_TRANSIT
    res_advance_1 = client.post(f"/api/v1/logistics/routes/{route_id}/advance", headers=log_headers)
    assert res_advance_1.status_code == 200
    assert res_advance_1.json()["status"] == "IN_TRANSIT"
    assert res_advance_1.json()["started_at"] is not None

    # 4. Attempt to advance to COMPLETED prematurely while delivery is still PENDING
    res_advance_premature = client.post(f"/api/v1/logistics/routes/{route_id}/advance", headers=log_headers)
    assert res_advance_premature.status_code == 400
    assert "pending Proof of Delivery" in res_advance_premature.json()["detail"]

    # 5. Get delivery record
    res_delivs = client.get(f"/api/v1/logistics/deliveries?route_id={route_id}", headers=log_headers)
    assert res_delivs.status_code == 200
    deliv_id = res_delivs.json()[0]["id"]

    # 6. Test invalid OTP format (alphanumeric / too short)
    res_bad_otp = client.post(f"/api/v1/logistics/deliveries/{deliv_id}/confirm", headers=log_headers, json={
        "verification_otp": "ABC",
        "temperature_at_delivery": 4.0
    })
    assert res_bad_otp.status_code == 400
    assert "Invalid verification OTP" in res_bad_otp.json()["detail"]

    # 7. Test invalid temperature reading (beyond physical safety scale)
    res_bad_temp = client.post(f"/api/v1/logistics/deliveries/{deliv_id}/confirm", headers=log_headers, json={
        "verification_otp": "4921",
        "temperature_at_delivery": 180.0
    })
    assert res_bad_temp.status_code == 400
    assert "Invalid food temperature" in res_bad_temp.json()["detail"]

    # 8. Valid delivery confirmation
    res_confirm = client.post(f"/api/v1/logistics/deliveries/{deliv_id}/confirm", headers=log_headers, json={
        "verification_otp": "4921",
        "temperature_at_delivery": 4.5,
        "recipient_sign_name": "Test NGO Verifier",
        "proof_of_delivery_image": "/uploads/pod/test.png"
    })
    assert res_confirm.status_code == 200
    assert res_confirm.json()["status"] == "DELIVERED"
    assert res_confirm.json()["delivered_time"] is not None

    # 9. Verify duplicate confirmation rejected (HTTP 400)
    res_dup_confirm = client.post(f"/api/v1/logistics/deliveries/{deliv_id}/confirm", headers=log_headers, json={
        "verification_otp": "4921",
        "temperature_at_delivery": 4.5
    })
    assert res_dup_confirm.status_code == 400
    assert "already been confirmed" in res_dup_confirm.json()["detail"]

    # 10. Complete route now that all deliveries are verified
    res_advance_final = client.post(f"/api/v1/logistics/routes/{route_id}/advance", headers=log_headers)
    assert res_advance_final.status_code == 200
    assert res_advance_final.json()["status"] == "COMPLETED"
    assert res_advance_final.json()["completed_at"] is not None


# =====================================================================
# DEFECT 3 & 6: ESG Metrics Source of Truth & Benchmarks
# =====================================================================

def test_esg_authoritative_calculation_no_double_counting():
    km_token = get_auth_token("kitchen@reserveai.com", "KITCHEN_MANAGER")
    headers = {"Authorization": f"Bearer {km_token}"}

    # Fetch sustainability summary
    res_summary = client.get("/api/v1/sustainability/summary", headers=headers)
    assert res_summary.status_code == 200
    data = res_summary.json()

    # Query DB directly to check actual verified deliveries
    db = SessionLocal()
    verified_requests = (
        db.query(RedistributionRequest)
        .join(Kitchen, RedistributionRequest.kitchen_id == Kitchen.id)
        .filter(Kitchen.organization_id == 1, RedistributionRequest.status == "DELIVERED")
        .all()
    )
    expected_kg = sum(r.quantity_kg for r in verified_requests)
    db.close()

    # Verify that reported rescued kg matches the actual delivered total exactly
    assert round(data["food_rescued_kg"], 1) == round(expected_kg, 1), (
        f"Double-counting detected: summary reported {data['food_rescued_kg']} kg, expected {expected_kg} kg"
    )


def test_esg_category_transparent_benchmarks():
    km_token = get_auth_token("kitchen@reserveai.com", "KITCHEN_MANAGER")
    headers = {"Authorization": f"Bearer {km_token}"}

    # Organization 1 has delivered records, so it returns actual verified categories
    res_org1 = client.get("/api/v1/sustainability/by-category?organization_id=1", headers=headers)
    assert res_org1.status_code == 200
    assert len(res_org1.json()) > 0
    # None of the categories should have "[Benchmark]" prefix since actual data exists
    for cat in res_org1.json():
        assert not cat["category"].startswith("[Benchmark]")
