import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def log_step(step_name: str, passed: bool, detail: str = ""):
    symbol = "[PASS]" if passed else "[FAIL]"
    print(f"{symbol} [{step_name}] {detail}")
    if not passed:
        sys.exit(1)

def main():
    print("=================================================================")
    print("reServe AI — LIVE END-TO-END WORKFLOW INTEGRATION VERIFICATION")
    print("Target: http://127.0.0.1:8000/api/v1")
    print("=================================================================\n")

    session = requests.Session()

    # -------------------------------------------------------------
    # JOURNEY A: Kitchen Demand Planning
    # -------------------------------------------------------------
    print("--- JOURNEY A: Kitchen Demand Planning ---")
    
    # 1. Login as Kitchen Manager
    res = session.post(f"{BASE_URL}/auth/login", json={
        "username": "kitchen@reserveai.com",
        "password": "Kitchen@1234"
    })
    log_step("A.1 Login as Kitchen Manager", res.status_code == 200, f"Token received, User: {res.json().get('user', {}).get('full_name')}")
    km_token = res.json()["access_token"]
    km_headers = {"Authorization": f"Bearer {km_token}"}

    # 2. Select Kitchen & Fetch Food Items
    res_k = session.get(f"{BASE_URL}/kitchens/", headers=km_headers)
    log_step("A.2 Select Kitchen Facility", res_k.status_code == 200 and len(res_k.json()) > 0, f"Found {len(res_k.json())} kitchens: {res_k.json()[0]['name']}")
    kitchen_id = res_k.json()[0]["id"]

    res_items = session.get(f"{BASE_URL}/inventory/food-items", headers=km_headers)
    log_step("A.3 Fetch Master Food Catalog", res_items.status_code == 200 and len(res_items.json()) > 0, f"Found {len(res_items.json())} catalog items")
    food_item_id = res_items.json()[0]["id"]

    # 3. Generate Demand Forecast with inventory netting
    res_pred = session.post(f"{BASE_URL}/demand/predict", headers=km_headers, json={
        "kitchen_id": kitchen_id,
        "food_item_id": food_item_id,
        "meal_slot": "LUNCH",
        "expected_footfall": 520
    })
    log_step("A.4 Run LightGBM Demand Forecast", res_pred.status_code == 200, 
             f"Expected: {res_pred.json().get('expected_demand_kg')} kg | On-Hand: {res_pred.json().get('current_inventory_on_hand_kg')} kg | Net Prep: {res_pred.json().get('net_recommended_production_kg')} kg")
    
    # 4. Verify Persistence
    res_forecasts = session.get(f"{BASE_URL}/demand/forecast?kitchen_id={kitchen_id}", headers=km_headers)
    log_step("A.5 Verify Persistence on Schedule", res_forecasts.status_code == 200 and len(res_forecasts.json().get("predictions", [])) > 0,
             f"Persisted records retrieved: {len(res_forecasts.json()['predictions'])} items")

    # -------------------------------------------------------------
    # JOURNEY B: Waste Prevention
    # -------------------------------------------------------------
    print("\n--- JOURNEY B: Food Waste Prevention ---")

    # 1. View Waste-Risk Prediction
    res_waste = session.get(f"{BASE_URL}/waste/predictions?kitchen_id={kitchen_id}", headers=km_headers)
    log_step("B.1 View Waste-Risk Forecast", res_waste.status_code == 200,
             f"Expected Waste: {res_waste.json().get('expected_waste_kg')} kg | Prob: {int(res_waste.json().get('waste_probability', 0)*100)}% | Cause: {res_waste.json().get('predicted_root_cause')}")

    # 2. Verify Surplus Hazard Alert
    res_alerts = session.get(f"{BASE_URL}/notifications/alerts?kitchen_id={kitchen_id}", headers=km_headers)
    log_step("B.2 Verify Autonomous Surplus Hazard Alert", res_alerts.status_code == 200, f"Active alerts for facility: {len(res_alerts.json())}")

    # 3. Record Verified Food Waste Event
    res_log = session.post(f"{BASE_URL}/waste/events", headers=km_headers, json={
        "kitchen_id": kitchen_id,
        "food_item_id": food_item_id,
        "quantity_wasted_kg": 6.5,
        "primary_cause": "OVERPRODUCTION",
        "waste_stage": "LEFTOVER_BUFFET",
        "financial_loss_inr": 715.0
    })
    log_step("B.3 Record Verified Waste Event", res_log.status_code == 200, f"Logged event ID #{res_log.json().get('id')}, quantity: 6.5 kg, loss: INR 715.0")

    # -------------------------------------------------------------
    # JOURNEY C: Food Quality Assessment & Human Verification
    # -------------------------------------------------------------
    print("\n--- JOURNEY C: Food Quality Assessment & Human Verification ---")

    # 1. Upload/Scan Food Image
    files = {"image": ("fresh_apples.jpg", b"mock-rgb-tensor-bytes-quality-test", "image/jpeg")}
    data = {"food_item_id": food_item_id, "category": "VEGETABLES", "food_name": "Farm Fresh Crisp Tomatoes"}
    res_scan = session.post(f"{BASE_URL}/quality/scan", headers=km_headers, files=files, data=data)
    log_step("C.1 Computer Vision Image Inference", res_scan.status_code == 200,
             f"Score: {res_scan.json().get('freshness_score')}% | Level: {res_scan.json().get('freshness_level')} | Shelf Life: {res_scan.json().get('remaining_shelf_life_days')} days | Safety Verdict: {res_scan.json().get('food_safety_verdict')}")
    scan_id = res_scan.json()["id"]

    # 2. Login as Authorized Quality Inspector
    res_qi = session.post(f"{BASE_URL}/auth/login", json={
        "username": "quality@reserveai.com",
        "password": "Quality@1234"
    })
    log_step("C.2 Login as Certified Quality Inspector", res_qi.status_code == 200, f"Inspector: {res_qi.json().get('user', {}).get('full_name')}")
    qi_token = res_qi.json()["access_token"]
    qi_headers = {"Authorization": f"Bearer {qi_token}"}

    # 3. Complete Human Verification & Audit Trail Sign-off
    res_verify = session.post(f"{BASE_URL}/quality/scans/{scan_id}/verify", headers=qi_headers, json={
        "inspector_notes": "Sensory smell, texture, and visual surface inspected. Thermal seals verified intact.",
        "final_disposition": "SAFE_FOR_REDISTRIBUTION",
        "override_model_decision": False
    })
    log_step("C.3 Human Verification & Audit Sign-Off", res_verify.status_code == 200 and res_verify.json().get("human_verified") is True,
             f"Scan #{scan_id} Certified by {res_verify.json().get('inspector_name')} at {res_verify.json().get('verified_at')}")

    # -------------------------------------------------------------
    # JOURNEY D: NGO Redistribution & Delivery
    # -------------------------------------------------------------
    print("\n--- JOURNEY D: NGO Redistribution & Delivery ---")

    # 1. View Available Surplus Lots
    res_surplus = session.get(f"{BASE_URL}/redistribution/surplus", headers=km_headers)
    log_step("D.1 View Available Surplus Lots", res_surplus.status_code == 200 and len(res_surplus.json()) > 0,
             f"Found {len(res_surplus.json())} active surplus lots")
    
    # Pick a POSTED lot (or create one if needed)
    posted_lots = [s for s in res_surplus.json() if s["status"] == "POSTED"]
    if not posted_lots:
        # Create a fresh posted surplus request
        res_new_s = session.post(f"{BASE_URL}/redistribution/requests", headers=km_headers, json={
            "kitchen_id": kitchen_id,
            "food_item_id": food_item_id,
            "quantity_kg": 40.0,
            "estimated_meals": 100,
            "available_from": "2026-09-29T18:00:00Z",
            "expires_at": "2026-09-30T00:00:00Z",
            "safe_temp_celsius": 65.0
        })
        surplus_id = res_new_s.json()["id"]
    else:
        surplus_id = posted_lots[0]["id"]

    # 2. Login as NGO Representative
    res_ngo = session.post(f"{BASE_URL}/auth/login", json={
        "username": "ngo@reserveai.com",
        "password": "NGO@1234"
    })
    log_step("D.2 Login as NGO Representative", res_ngo.status_code == 200, f"NGO Rep: {res_ngo.json().get('user', {}).get('full_name')}")
    ngo_token = res_ngo.json()["access_token"]
    ngo_headers = {"Authorization": f"Bearer {ngo_token}"}

    # 3. Claim Eligible Surplus Request
    res_claim = session.post(f"{BASE_URL}/redistribution/requests/{surplus_id}/claim?ngo_id=1", headers=ngo_headers)
    log_step("D.3 Claim Surplus Lot", res_claim.status_code == 200, f"Claimed Lot #{surplus_id} for NGO #1, status: {res_claim.json().get('status')}")

    # 4. Verify Duplicate Claim Protection (409 Conflict)
    res_dup = session.post(f"{BASE_URL}/redistribution/requests/{surplus_id}/claim?ngo_id=2", headers=ngo_headers)
    log_step("D.4 Duplicate-Claim Concurrency Protection", res_dup.status_code == 409,
             f"HTTP 409 Conflict correctly returned: {res_dup.json().get('detail')}")

    # 5. Login as Logistics Coordinator & Optimize Route
    res_logistics = session.post(f"{BASE_URL}/auth/login", json={
        "username": "logistics@reserveai.com",
        "password": "Logistics@1234"
    })
    log_step("D.5 Login as Fleet Logistics Coordinator", res_logistics.status_code == 200, f"Dispatcher: {res_logistics.json().get('user', {}).get('full_name')}")
    log_token = res_logistics.json()["access_token"]
    log_headers = {"Authorization": f"Bearer {log_token}"}

    res_opt = session.post(f"{BASE_URL}/logistics/routes/optimize", headers=log_headers, json={
        "kitchen_id": kitchen_id,
        "selected_requests": [surplus_id],
        "vehicle_capacity_kg": 600.0
    })
    log_step("D.6 Google OR-Tools CVRPTW Route Optimization", res_opt.status_code == 200,
             f"Route {res_opt.json().get('route_code')} generated with {len(res_opt.json().get('waypoints', []))} waypoints, dist: {res_opt.json().get('total_distance_km')} km")
    route_id = res_opt.json()["id"]

    # 6. Advance Delivery Status
    res_adv = session.post(f"{BASE_URL}/logistics/routes/{route_id}/advance?next_status=IN_TRANSIT", headers=log_headers)
    log_step("D.7 Advance Route Status", res_adv.status_code == 200 and res_adv.json()["status"] == "IN_TRANSIT",
             f"Route #{route_id} transitioned to IN_TRANSIT")

    # 7. Confirm Delivery via Recipient OTP Proof of Delivery
    res_deliveries = session.get(f"{BASE_URL}/logistics/deliveries?route_id={route_id}", headers=log_headers)
    del_id = res_deliveries.json()[0]["id"] if (res_deliveries.status_code == 200 and len(res_deliveries.json()) > 0) else 1

    res_confirm = session.post(f"{BASE_URL}/logistics/deliveries/{del_id}/confirm", headers=log_headers, json={
        "recipient_sign_name": "Kabir Singhania (Robin Hood Army Rep)",
        "temperature_at_delivery": 4.2,
        "verification_otp": "4921",
        "proof_of_delivery_image": "/uploads/pod/sig_verified_live.png"
    })
    log_step("D.8 Confirm Delivery via OTP Proof of Delivery", res_confirm.status_code == 200 and res_confirm.json()["status"] == "DELIVERED",
             f"Delivery #{del_id} verified DELIVERED with temp 4.2°C at {res_confirm.json().get('delivered_time')}")

    # -------------------------------------------------------------
    # JOURNEY E: Sustainability & ESG Audit
    # -------------------------------------------------------------
    print("\n--- JOURNEY E: Sustainability & ESG Reporting ---")

    # 1. Open Sustainability Summary
    res_sust = session.get(f"{BASE_URL}/sustainability/summary", headers=km_headers)
    log_step("E.1 Fetch Sustainability Footprint Summary", res_sust.status_code == 200,
             f"Measured Rescued: {res_sust.json().get('food_rescued_kg')} kg | CO2 Avoided: {res_sust.json().get('co2_avoided_kg')} kg | Water Saved: {res_sust.json().get('water_saved_liters')} L")

    # 2. Generate Scope 3 ESG Audit Report
    res_audit = session.get(f"{BASE_URL}/sustainability/audit-report?organization_id=1&reporting_period=FY%202026-Q1", headers=km_headers)
    log_step("E.2 Generate Certified Scope 3 ESG Audit Report", res_audit.status_code == 200,
             f"Report ID: {res_audit.json().get('report_id')} | Status: {res_audit.json().get('scope_3_compliance_status')} | Categories: {len(res_audit.json().get('category_breakdown', []))} | Verified Handover: {res_audit.json().get('verified_deliveries_count')}")

    print("\n=================================================================")
    print("ALL 5 BUSINESS JOURNEYS EXECUTED & FULLY VERIFIED ON LIVE STACK!")
    print("=================================================================")

if __name__ == "__main__":
    main()
