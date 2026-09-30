# ReServeAI — Core API Reference

## 1. Authentication Endpoints

### `POST /api/v1/auth/login`
- **Request:** `{"username": "user@example.com", "password": "Password@123"}`
- **Response:** `{"access_token": "...", "token_type": "bearer", "expires_in": 86400, "user": {...}}`
- **Rate Limit:** 10 requests / minute in production (HTTP 429 when exceeded).

### `POST /api/v1/auth/register`
- **Request:** `{"email": "user@example.com", "password": "Password@123", "full_name": "Jane Doe"}`
- **Response:** `{"id": 1, "email": "user@example.com", "role": "PUBLIC_USER", ...}`
- **Security:** Rejects client attempts to assign non-`PUBLIC_USER` roles.

### `GET /api/v1/auth/me`
- **Headers:** `Authorization: Bearer <JWT>`
- **Response:** Returns current authenticated user record.

---

## 2. Health & Telemetry Probes

### `GET /health/live`
- **Purpose:** Kubernetes liveness probe.
- **Response:** `200 OK` (`{"status": "ALIVE", "process": "running"}`)

### `GET /health/ready`
- **Purpose:** Dependency readiness probe.
- **Response:** `200 OK` with individual component statuses (`application`, `database`, `authentication`, `model_registry`, `demand`, `maintenance`, `energy`, `enose`, `fruit_cv`, `waste`, `routing`).
- **Failure:** `503 Service Unavailable` if database connectivity is broken.

### `GET /health`
- **Purpose:** Legacy container healthcheck.
- **Response:** `200 OK` (`{"status": "HEALTHY", "database": "connected"}`)

---

## 3. Machine Learning & Optimization Endpoints

### `GET /api/v1/ml/status`
- **Headers:** `Authorization: Bearer <JWT>`
- **Response:** Live registry state, artifact presence, and engine health across all 8 modules.

### `POST /api/v1/demand/predict`
- **Payload:** `{"kitchen_id": 1, "food_item_id": 1, "day_of_week": 2, "is_weekend": false, "historical_avg_demand": 45.0, "current_stock": 20.0}`
- **Response:** LightGBM demand forecast (`expected_demand_kg`, `confidence_score`).

### `POST /api/v1/maintenance/evaluate`
- **Payload:** `{"air_temperature_k": 298.1, "process_temperature_k": 308.6, "rotational_speed_rpm": 1500, "torque_nm": 40.0, "tool_wear_min": 15, "machine_type": "M"}`
- **Response:** Equipment failure probability and maintenance classification.

### `POST /api/v1/energy/predict`
- **Payload:** Appliances and environmental features (temperatures, humidities, wind speed).
- **Response:** Predicted energy consumption in Watt-hours (`predicted_energy_wh`).

### `POST /api/v1/sensors/enose/evaluate`
- **Scope:** **BEEF QUALITY ONLY** (Mendeley E-Nose Dataset).
- **Payload:** Temperature, Humidity, and 8 MQ sensor values (`mq2`, `mq3`, `mq4`, `mq5`, `mq135`-`mq138`).
- **Response:** 4-class quality verdict (`EXCELLENT`, `GOOD`, `ACCEPTABLE`, `SPOILED`).

### `POST /api/v1/quality/scan`
- **Payload:** Multipart form data (`image` file, `food_item_id`).
- **Status:** **SIMULATED** (`spectral-spatial-v2.1-SIMULATED`).
- **Response:** Freshness score, defect detection, simulation notice, and mandatory `human_verified=False` flag.

### `GET /api/v1/waste/predictions`
- **Status:** **RULE-BASED FALLBACK** (`rule-based-v1.0`).
- **Response:** Expected waste estimation by kitchen and root-cause breakdown.

### `POST /api/v1/logistics/optimize-route`
- **Engine:** Clarke-Wright Savings + 2-Opt local search heuristics.
- **Response:** Sequence of stops, total distance, estimated travel time, 100% capacity feasibility.

---

## 4. Operational Endpoints
- `GET /api/v1/inventory/`: Active inventory batches.
- `GET /api/v1/redistribution/surplus`: Surplus batches open for NGO reservation.
- `GET /api/v1/logistics/routes`: Active delivery routes.
- `POST /api/v1/logistics/deliveries/{id}/confirm`: OTP proof-of-delivery sign-off.
- `GET /api/v1/sustainability/summary`: Carbon emissions avoided, water saved, and diverted meals.
