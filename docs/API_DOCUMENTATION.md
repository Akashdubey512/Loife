# reServe AI — Complete REST API Documentation

Base URL: `/api/v1`
Interactive Swagger UI: `http://localhost:8000/docs`
OpenAPI JSON: `http://localhost:8000/openapi.json`

All authenticated endpoints require an `Authorization` header formatted as:
`Authorization: Bearer <JWT_ACCESS_TOKEN>`

---

## 1. Authentication & Tenant Identity

### `POST /auth/login`
Authenticates a user and issues an HMAC-SHA256 JWT access token.
- **Request Body (JSON or Form)**:
  ```json
  {
    "username": "admin@reserveai.com",
    "password": "Admin@1234"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "admin@reserveai.com",
      "full_name": "Dr. Vikram Malhotra",
      "role": "SUPER_ADMIN",
      "organization_id": 1
    }
  }
  ```

### `GET /auth/me`
Retrieves authenticated user profile and permissions.
- **Response `200 OK`**:
  ```json
  {
    "id": 1,
    "email": "admin@reserveai.com",
    "full_name": "Dr. Vikram Malhotra",
    "role": "SUPER_ADMIN",
    "organization_id": 1,
    "phone_number": "+91 98111 22334",
    "is_active": true
  }
  ```

---

## 2. Demand Forecasting (Workflow A)

### `GET /demand/forecast`
Generates itemized demand prediction and net production recommendations.
- **Query Parameters**:
  - `kitchen_id` (int, default: 1)
  - `target_date` (date, optional)
- **Response `200 OK`**:
  ```json
  {
    "kitchen_id": 1,
    "target_date": "2026-09-30",
    "predictions": [
      {
        "food_item_id": 1,
        "food_name": "Basmati Rice & Dal Makhani",
        "expected_demand_kg": 182.4,
        "confidence_score": 0.94,
        "recommended_production_kg": 154.4,
        "surplus_risk_probability": 0.08,
        "model_version": "lgbm-v1.4"
      }
    ]
  }
  ```

---

## 3. Waste Prevention & Alerts (Workflow B)

### `GET /waste/predictions`
Calculates imminent surplus risk and prescribes prevention workflows.
- **Query Parameters**:
  - `kitchen_id` (int, required)
- **Response `200 OK`**:
  ```json
  {
    "kitchen_id": 1,
    "forecast_date": "2026-09-29",
    "expected_waste_kg": 78.0,
    "waste_probability": 0.71,
    "predicted_root_cause": "EXCESS_PREPARATION_OVER_STUDENT_FOOTFALL",
    "prevention_recommendation": "HALT_SECONDARY_BATCH_PREP_IMMEDIATELY"
  }
  ```

### `POST /waste/events`
Logs actual kitchen waste and automatically decrements inventory.
- **Request Body**:
  ```json
  {
    "kitchen_id": 1,
    "food_item_id": 1,
    "batch_id": 101,
    "quantity_wasted_kg": 12.5,
    "waste_stage": "POST_SERVICE_SURPLUS",
    "primary_cause": "UNCONSUMED_HELD_FOOD",
    "financial_loss_inr": 1375.0
  }
  ```

---

## 4. Food Quality Assessment & Multi-Factor Safety (Workflow C)

### `POST /quality/scan`
Executes EfficientNet-B0 visual inference with cold-chain sensor validation.
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `image` or `file` (Binary Image File)
  - `food_item_id` (int)
  - `category` (string, optional)
  - `food_name` (string, optional)
  - `batch_id` (int, optional)
- **Response `200 OK`**:
  ```json
  {
    "id": 401,
    "food_item_id": 1,
    "food_name": "Farm Fresh Tomatoes",
    "image_url": "/uploads/scans/tomato.jpg",
    "freshness_score": 94.6,
    "freshness_level": "FRESH",
    "remaining_shelf_life_days": 4.8,
    "redistribution_status": "SAFE_FOR_REDISTRIBUTION",
    "confidence": 0.965,
    "inspected_at": "2026-09-29T12:00:00Z",
    "defects_detected": [],
    "sensor_safety_cleared": true,
    "human_verified": false,
    "food_safety_verdict": "PENDING_HUMAN_VERIFICATION"
  }
  ```

### `POST /quality/scans/{scan_id}/verify`
Human inspector sign-off certifying batch compliance for redistribution.
- **Request Body**:
  ```json
  {
    "verdict": "APPROVED_FOR_REDISTRIBUTION",
    "inspector_notes": "Sensory smell and firmness inspected. Clear for donation.",
    "override_model_decision": false
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "scan_id": 401,
    "status": "SAFE_FOR_REDISTRIBUTION",
    "food_safety_verdict": "APPROVED_FOR_REDISTRIBUTION",
    "verified_by_user_id": 3,
    "verified_at": "2026-09-29T12:05:00Z",
    "notes": "Sensory smell and firmness inspected. Clear for donation."
  }
  ```

---

## 5. Surplus Redistribution & Fleet Logistics (Workflow D)

### `GET /redistribution/surplus`
Lists all active surplus lots ready for NGO pairing.

### `POST /redistribution/match/{request_id}`
Computes multi-factor compatibility ranking of nearby verified food recovery NGOs.

### `POST /redistribution/claim/{request_id}` (Alias: `/redistribution/requests/{request_id}/claim`)
Pairs surplus lot with selected NGO. Enforces concurrency lock to prevent duplicate claims.
- **Query Parameter**: `ngo_id` (int)
- **Response `200 OK`**:
  ```json
  {
    "message": "Surplus lot #1 claimed by Robin Hood Army",
    "status": "MATCHED",
    "matched_ngo_id": 1
  }
  ```
- **Response `409 Conflict`**: If lot is already claimed.

### `POST /logistics/routes/optimize` (Alias: `/logistics/optimize`)
Solves multi-stop Capacitated Vehicle Routing Problem (CVRPTW) via Google OR-Tools.
- **Request Body**:
  ```json
  {
    "kitchen_id": 1,
    "selected_requests": [1, 2],
    "vehicle_capacity_kg": 500.0
  }
  ```
- **Response `200 OK`**: Returns route code, distance, duration, and ordered waypoints.

### `POST /logistics/deliveries/{delivery_id}/confirm`
Digital Proof of Delivery (PoD) handover verification.
- **Request Body**:
  ```json
  {
    "recipient_sign_name": "Sister Anita (Shelter Director)",
    "temperature_at_delivery": 3.6,
    "verification_otp": "4921",
    "proof_of_delivery_image": "/uploads/pod/sig.png"
  }
  ```

---

## 6. Sustainability Accounting & ESG Audit (Workflow E)

### `GET /sustainability/summary`
Calculates cumulative environmental impact using Poore & Nemecek lifecycle multipliers.

### `GET /sustainability/audit-report`
Generates comprehensive Scope 3 ESG Audit Certificate.
- **Query Parameters**:
  - `organization_id` (int, default: 1)
  - `reporting_period` (string, default: "FY 2026-Q1")
- **Response `200 OK`**:
  ```json
  {
    "report_id": "ESG-202609-F4C9B10A",
    "organization_name": "Apex Institutional Dining Cluster",
    "audit_date": "2026-09-29T12:00:00Z",
    "reporting_period": "FY 2026-Q1",
    "measured_rescued_kg": 4250.0,
    "pipeline_potential_kg": 83.0,
    "co2e_avoided_kg": 10625.0,
    "virtual_water_conserved_liters": 2125000.0,
    "land_use_prevented_sqm": 8500.0,
    "meals_served_to_needy": 8500,
    "equivalent_trees_planted": 488.1,
    "car_km_emissions_offset": 55338.5,
    "verified_deliveries_count": 142,
    "scope_3_compliance_status": "AUDITED_AND_COMPLIANT_GHG_CAT_1",
    "methodology": "Poore & Nemecek (2018) Science LCA Multipliers; WRAP UK Food Waste & GHG Equivalents; IPCC AR6 GWP100.",
    "category_breakdown": [],
    "assumptions": []
  }
  ```
