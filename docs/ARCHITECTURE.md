# reServe AI — End-to-End System Architecture

## 1. Executive Summary & Vision

**reServe AI** is an enterprise-grade circular food waste reduction and sustainable redistribution platform. It integrates:
- **Intelligent Demand Forecasting**: Preventing overproduction before raw ingredients are cooked.
- **Predictive Waste Mitigation**: Early risk detection of surplus and automated kitchen dispatch alerts.
- **Computer Vision Freshness & Multi-Factor Safety**: Optical CNN freshness classification paired with IoT cold-chain logging and certified human inspection clearance.
- **Autonomous NGO Redistribution Network**: Fair-allocation matching algorithm with duplicate-claim prevention and geofenced dispatch.
- **Smart Fleet Logistics**: Capacitated Vehicle Routing with Time Windows (CVRPTW) optimized via Google OR-Tools.
- **Poore & Nemecek (2018) ESG Lifecycle Accounting**: Transparent, auditable Scope 3 greenhouse gas avoidance calculations separating physically verified deliveries from pipeline potential.

---

## 2. High-Level Component Topology

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 Enterprise Web Client                  │
                  │         React 19 + TypeScript + Tailwind CSS v4        │
                  │   (Executive, Kitchen, Quality, Logistics, ESG Dashboards)│
                  └───────────────────────────┬────────────────────────────┘
                                              │ HTTP / JSON & SSE / WS
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │                  Reverse Proxy (Nginx)                 │
                  │          Port 80 (Web Client) / Port 3000              │
                  └─────────────┬────────────────────────────┬─────────────┘
                                │ /api/v1/                   │ /ws/
                                ▼                            ▼
                  ┌────────────────────────────────────────────────────────┐
                  │              Core Backend Service (FastAPI)            │
                  │             Python 3.11/3.13 — Port 8000               │
                  │  - JWT Bearer Authentication & RBAC Governance         │
                  │  - Multi-Tenant Isolation & Transaction Locking        │
                  │  - Business Workflow Orchestrators (A through E)       │
                  └─────────┬──────────────┬──────────────┬──────────────┬─┘
                            │              │              │              │
      ┌─────────────────────┘              │              │              └─────────────────────┐
      ▼                                    ▼              ▼                                    ▼
┌──────────────┐                  ┌────────────────┐ ┌────────────────┐              ┌────────────────┐
│  PostgreSQL  │                  │  Redis Broker  │ │  ML Service    │              │ IoT Telemetry  │
│ 15 Database  │                  │  Cache / PubSub│ │ LightGBM / XGB │              │ Edge Streaming │
│ (23 Tables)  │                  │  (Port 6379)   │ │  (Port 8001)   │              │ MQTT / Webhook │
└──────────────┘                  └────────────────┘ └────────────────┘              └────────────────┘
```

---

## 3. Core Business Workflows

### Workflow A: Intelligent Food Demand Planning
1. **Inputs**: Historical consumption (7-day lag, rolling average), calendar shift, price elasticities, and kitchen stock on hand.
2. **Inference**: LightGBM/pure-Python demand forecasting engine estimates `expected_demand_kg` with uncertainty confidence intervals.
3. **Inventory Cross-Reference**: Kitchen current inventory is subtracted from gross expected demand to yield `recommended_production_kg`.
4. **Persistence & Tenant Scoping**: Results persisted to `DemandPrediction` scoped strictly to `organization_id` and `kitchen_id`.
5. **Dashboard Visualization**: Shift chef receives real-time production recommendations.

### Workflow B: Food Waste Prevention
1. **Inputs**: Scheduled production batches, real-time demand forecast, and inventory batches nearing expiration (<14 hours).
2. **Inference**: Multi-variable XGBoost waste model calculates `expected_waste_kg` and `surplus_risk_probability`.
3. **Alert Triggering**: If surplus risk exceeds 20%, an automated high-severity `Alert` is generated.
4. **Inventory Deductions**: Actual recorded waste events automatically deduct remaining stock from `InventoryBatch`.

### Workflow C: Food Quality Assessment & Multi-Factor Safety Clearance
1. **Inputs**: Visual snapshot + food category + real-time cold-chain sensor readings.
2. **Preprocessing**: Normalized to RGB 224x224 spectral tensor.
3. **Visual Inference**: EfficientNet-B0 extracts surface degradation, mold mycelium, and color absorbance to output a freshness score (0-100%) and shelf-life estimate.
4. **Independent Safety Checks**:
   - Expiration date validation (expired batches rejected regardless of appearance).
   - Cold-chain anomaly logs (temperature spikes > 8°C in past 24 hours downgrade disposition).
5. **Human Inspector Sign-Off**: Certified Food Safety Officer verifies sensory traits and signs off digitally before surplus can be distributed.

### Workflow D: Surplus Redistribution & CVRPTW Routing
1. **Surplus Registration**: Kitchen manager posts excess verified edible surplus.
2. **Compatibility Ranking**: Autonomous engine ranks verified NGO partners based on haversine distance, daily meal capacity, cold-chain availability, and trust rating.
3. **Concurrency Locking & Duplicate Prevention**: Single-claim guarantee with database row locks preventing double-allocation.
4. **CVRPTW Route Optimization**: Google OR-Tools dynamically solves vehicle route with multi-stop waypoints, capacity bounds (500 kg), and shelf-life delivery time windows.
5. **Digital Proof of Delivery (PoD)**: Driver verifies recipient handover using 4-digit OTP and calibrated arrival food temperature.

### Workflow E: ESG Sustainability Accounting & Scope 3 Audit
1. **Verified Deliveries Only**: Only physical handovers with status `DELIVERED` count toward verified ESG metrics; in-transit lots are classified as pipeline potential.
2. **Poore & Nemecek (Science 2018) LCA Factors**:
   - Cooked Institutional Meals: 2.5 kg CO2e / kg, 500 L water / kg, 2.0 m² land / kg.
   - Fresh Vegetables: 0.5 kg CO2e / kg, 322 L water / kg, 0.4 m² land / kg.
   - Dairy & Paneer: 3.2 kg CO2e / kg, 628 L water / kg, 4.5 m² land / kg.
   - Bakery Products: 1.6 kg CO2e / kg, 1100 L water / kg, 1.8 m² land / kg.
3. **Equivalency Calculations**: Mature tree absorption (21.77 kg CO2/year) and passenger car offsets (192g CO2/km).
4. **Audit Report Export**: Dynamic generation of SHA-verified ESG Audit Certificates for corporate reporting.

---

## 4. Multi-Tenant Security & Role-Based Access Control (RBAC)

The platform supports 6 distinct roles:
1. `SUPER_ADMIN`: Global platform oversight, cross-institution audits, and tenant onboarding.
2. `ORG_ADMIN`: Organization-level compliance management and kitchen administration.
3. `KITCHEN_MANAGER`: Inventory management, prep logging, demand visualization, and surplus registration.
4. `QUALITY_INSPECTOR`: Visual food scanning and mandatory human sign-off certification.
5. `LOGISTICS_COORDINATOR`: Fleet route optimization, vehicle dispatch, and live GPS monitoring.
6. `NGO_REP`: Surplus matching response, delivery pickup, and OTP recipient verification.

Multi-tenant isolation is enforced at the database session and FastAPI dependency level via `check_tenant_access(user, organization_id)`. Any unauthorized cross-tenant attempt receives `403 Forbidden`.
