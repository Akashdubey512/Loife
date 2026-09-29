# reServe AI - API Contract Specification (OpenAPI / REST + WebSockets)
## Base Endpoint: `/api/v1`

---

## 1. Authentication & Users (`/auth`, `/users`)

### `POST /auth/login`
- **Description**: Authenticate user and issue JWT Access Token.
- **Request Body**:
  ```json
  {
    "username": "admin@reserveai.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "email": "admin@reserveai.com",
      "full_name": "Executive Admin",
      "role": "SUPER_ADMIN",
      "organization_id": 1
    }
  }
  ```

### `GET /users/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response `200 OK`**: Current user profile and permission set.

---

## 2. Kitchens & Facilities (`/kitchens`, `/organizations`)

### `GET /kitchens`
- **Query Params**: `organization_id=1`, `limit=20`
- **Response `200 OK`**: List of kitchens with operational capacity and status.

### `GET /kitchens/{kitchen_id}/overview`
- **Response `200 OK`**: Real-time snapshot of active production batches, sensor health, and pending surplus.

---

## 3. Inventory & Batches (`/inventory`)

### `GET /inventory`
- **Query Params**: `kitchen_id=1`, `status=NEARING_EXPIRY`
- **Response `200 OK`**: List of current inventory stocks with batch expiry breakdown.

### `POST /inventory/batches`
- **Description**: Register a newly procured or processed batch.
- **Request Body**:
  ```json
  {
    "inventory_id": 12,
    "batch_number": "BATCH-2026-09-001",
    "quantity_kg": 45.5,
    "expiry_date": "2026-10-02T12:00:00Z"
  }
  ```

---

## 4. Production & Demand Planning (`/demand`, `/production`)

### `GET /demand/forecast`
- **Description**: Returns 7-day predicted food demand powered by LightGBM model.
- **Query Params**: `kitchen_id=1`, `date=2026-09-30`, `meal_slot=LUNCH`
- **Response `200 OK`**:
  ```json
  {
    "prediction_date": "2026-09-30",
    "meal_slot": "LUNCH",
    "kitchen_id": 1,
    "predictions": [
      {
        "food_item_id": 3,
        "food_name": "Steamed Basmati Rice & Dal Makhani",
        "expected_demand_kg": 182.4,
        "confidence_score": 0.94,
        "recommended_production_kg": 190.0,
        "surplus_risk_probability": 0.08
      }
    ]
  }
  ```

### `POST /production/batches`
- **Description**: Log or update kitchen production plans.

---

## 5. Waste Analytics & Prediction (`/waste`)

### `GET /waste/predictions`
- **Description**: Predict anticipated waste per production cycle and highlight root causes.
- **Response `200 OK`**:
  ```json
  {
    "kitchen_id": 1,
    "forecast_date": "2026-09-30",
    "total_expected_waste_kg": 14.2,
    "waste_probability": 0.22,
    "primary_risk_factor": "Overproduction in non-vegetarian meal slot",
    "mitigation_action": "Reduce prep batch by 15kg; adjust prep to live footfall count."
  }
  ```

### `POST /waste/events`
- **Description**: Record actual waste event for ESG audit logging.

---

## 6. Computer Vision Freshness (`/quality`)

### `POST /quality/scan`
- **Content-Type**: `multipart/form-data`
- **Form Fields**: `file` (Image file), `food_item_id` (int), `batch_id` (optional int)
- **Response `200 OK`**:
  ```json
  {
    "scan_id": 401,
    "food_item": "Fresh Tomatoes & Bell Peppers",
    "freshness_score": 92.4,
    "freshness_level": "FRESH",
    "remaining_shelf_life_days": 4.5,
    "redistribution_status": "SAFE_FOR_REDISTRIBUTION",
    "confidence": 0.96,
    "defects_detected": [],
    "inspected_at": "2026-09-29T16:54:00Z"
  }
  ```

---

## 7. IoT Sensors & Smart Storage (`/sensors`, `/energy`, `/maintenance`)

### `POST /sensors/readings`
- **Description**: Ingest telemetry from IoT gateway (temperature, humidity, methane).
- **Request Body**:
  ```json
  {
    "kitchen_id": 1,
    "sensor_id": "SN-TEMP-04",
    "sensor_type": "TEMPERATURE",
    "value": 4.2,
    "unit": "°C",
    "storage_zone": "Walk-in Cold Room 2"
  }
  ```

### `GET /sensors/live`
- **Description**: Real-time sensory readings with breach warning indicators.

### `GET /maintenance/health`
- **Description**: Predictive equipment maintenance inference (AI4I CatBoost model).
- **Response `200 OK`**:
  ```json
  {
    "machines": [
      {
        "machine_id": "BLAST-CHILLER-01",
        "machine_type": "BLAST_CHILLER",
        "failure_probability": 0.04,
        "status": "HEALTHY",
        "recommended_action": "Standard scheduled inspection in 14 days"
      }
    ]
  }
  ```

---

## 8. Redistribution & Logistics Engine (`/redistribution`, `/logistics`)

### `GET /redistribution/surplus`
- **Description**: Fetch all available surplus batches ready for claim.

### `POST /redistribution/match`
- **Description**: Triggers automated multi-factor matching between available surplus and active NGOs.
- **Request Body**:
  ```json
  {
    "request_id": 105,
    "max_distance_km": 15.0
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "request_id": 105,
    "recommended_matches": [
      {
        "ngo_id": 4,
        "ngo_name": "Robin Hood Army - Central Hub",
        "compatibility_score": 98.2,
        "distance_km": 4.2,
        "capacity_available": 350,
        "has_cold_chain": true,
        "eta_pickup_minutes": 25
      }
    ]
  }
  ```

### `POST /logistics/optimize-route`
- **Description**: Compute OR-Tools optimized multi-point pickup and drop-off route.

---

## 9. Sustainability Intelligence (`/sustainability`, `/analytics`)

### `GET /sustainability/summary`
- **Description**: Aggregated life-cycle analysis (Poore & Nemecek coefficients).
- **Response `200 OK`**:
  ```json
  {
    "timeframe": "LAST_30_DAYS",
    "food_rescued_kg": 4250.0,
    "co2_avoided_kg": 10625.0,
    "water_saved_liters": 2125000.0,
    "land_use_prevented_sqm": 8500.0,
    "financial_savings_inr": 467500.0,
    "meals_served_to_needy": 8500,
    "esg_score_contribution": "+18.4%"
  }
  ```

---

## 10. WebSockets Real-Time Stream (`/ws`)

### `WS /ws/telemetry`
- **Client -> Server**: `{ "action": "subscribe", "channels": ["kitchen_1_sensors", "surplus_alerts", "logistics_live"] }`
- **Server -> Client**: Emits live sensor updates, threshold breach alarms, and delivery telemetry.
