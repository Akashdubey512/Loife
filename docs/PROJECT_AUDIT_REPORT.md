# reServe AI — Complete Project Architecture & Technical Audit Report
**Enterprise AI-Powered Food Waste Reduction & Sustainable Redistribution Platform**  
**Smart India Hackathon (SIH 2026) Enterprise Edition**

---

## 1. Executive Summary & Problem Domain

### 1.1 The Global & National Challenge
Across the food supply chain, over one-third of all food produced is lost or discarded globally, driving **8–10% of global greenhouse gas emissions** and wasting billions of cubic meters of fresh water and energy. In India, institutional catering systems—including university hostels and mess halls, large corporate IT campuses, hospital kitchens, and central banquet facilities—face chronic volatility:
- **Demand unpredictability**: Footfall fluctuates based on exam schedules, weather, weekends, and holidays, leading to chronic overproduction (typically 15–25% excess prep).
- **Perishable shelf-life decay**: Lack of objective, scientific shelf-life assessment results in either premature disposal of edible food or hazardous distribution of degraded items.
- **Fragmented redistribution**: Donating surplus food to local NGOs (e.g., Robin Hood Army, Feeding India) is typically handled via ad-hoc phone calls, lacking verification, cold-chain safety monitoring, and vehicle route optimization.
- **Missing ESG traceability**: Institutional ESG reporting under BRSR (Business Responsibility and Sustainability Reporting) and GHG Protocol Scope 3 lacks auditable metrics on food waste diversion, methane avoidance, and virtual water conservation.

### 1.2 The reServe AI Solution
**reServe AI** is a production-grade, enterprise SaaS platform that transforms linear, wasteful food operations into an intelligent, closed-loop circular redistribution network. The system delivers:
1. **Predictive Pre-Prep Optimization**: LightGBM machine learning models forecast sub-meal demand to prevent food waste before cooking begins.
2. **Computer Vision Quality Grading**: EfficientNet-B0 visual scanning inspects surface oxidation and cellular decay to assign an objective Freshness Index (0–100) and Safe Redistribution Window.
3. **Continuous Cold-Chain IoT Telemetry**: Sensor streaming monitors ambient temperature, relative humidity, power draw, and volatile organic compounds (methane/ammonia) with sub-second threshold breach alerts.
4. **Autonomous NGO Matching & Dispatch**: An automated matching engine pairs validated food batches with nearby verified charities based on dietary capacity, distance, storage type, and urgency.
5. **Route & Fleet Optimization**: Vehicle routing algorithms plan multi-stop, capacity-constrained pickups to minimize transit time and carbon footprint.
6. **Poore & Nemecek ESG Life-Cycle Accounting**: Scientific conversion of diverted food mass into kilograms of CO₂ equivalent avoided and liters of virtual water conserved, generating downloadable compliance audit certificates.

---

## 2. End-to-End System Architecture

```mermaid
flowchart TB
    subgraph Clients["Presentation Layer (Port 3000)"]
        UI_Admin["Super Admin Dashboard"]
        UI_Kitchen["Kitchen Manager Dashboard"]
        UI_QA["Quality Inspector Console"]
        UI_Logistics["Logistics Dispatch Map"]
        UI_NGO["NGO Redistribution Portal"]
    end

    subgraph Gateway["API & Security Layer (Port 8000)"]
        ReverseProxy["Vite Dev Proxy / Nginx Gateway"]
        AuthModule["OAuth2 / JWT Auth Engine"]
        RBAC["RBAC Middleware (Role Enforcement)"]
        RateLimiter["In-Memory Sliding-Window Rate Limiter"]
    end

    subgraph CoreServices["FastAPI Application Services"]
        DemandSvc["Demand Forecast Service"]
        QualitySvc["CV Freshness Scan Service"]
        WasteSvc["Waste Analytics Engine"]
        RedistSvc["NGO Matching & Claim Engine"]
        LogisticsSvc["Routing & Fleet Engine"]
        IoT_Svc["Sensor & Telemetry Ingestion"]
        ESG_Svc["Poore & Nemecek Sustainability Engine"]
        NotifySvc["WebSocket Push Notification Hub"]
    end

    subgraph DataStorage["Data & State Persistence"]
        RelationalDB[("PostgreSQL / SQLite Database\n(23 Relational Tables)")]
        RedisCache[("Redis Caching & PubSub\n(Optional / Port 6379)")]
    end

    subgraph AI_Edge["AI & Microservice Services"]
        ML_Microservice["LightGBM & XGBoost Engine (Port 8001)"]
        CV_Engine["EfficientNet Freshness Model (ONNX)"]
        Edge_Simulator["IoT ESP32 Sensor Telemetry Streamer"]
    end

    Clients --> ReverseProxy
    ReverseProxy --> Gateway
    Gateway --> AuthModule --> RBAC --> RateLimiter
    RateLimiter --> CoreServices
    CoreServices --> RelationalDB
    CoreServices --> RedisCache
    CoreServices --> AI_Edge
    CoreServices --> NotifySvc
    NotifySvc -.-> Clients
```

---

## 3. Technology Stack Breakdown

| Layer | Technologies & Frameworks | Description |
| :--- | :--- | :--- |
| **Backend API** | **Python 3.11 / 3.13**, **FastAPI**, **Uvicorn**, **Pydantic v2** | High-performance asynchronous REST API with automatic OpenAPI documentation (`/api/v1/docs`). |
| **Database & ORM** | **SQLAlchemy 2.0**, **SQLite 3** (local/demo), **PostgreSQL 15** (production) | 23 relational database entities with connection pooling, declarative schemas, and foreign-key constraints. |
| **Authentication & Security** | **JWT (python-jose)**, **Passlib (Argon2 / Bcrypt)**, **OAuth2PasswordBearer** | Stateless bearer authentication with role-based token payloads, strict role guards, and sliding-window rate limiting. |
| **Frontend Web Console** | **React 19**, **TypeScript 5.8+**, **Vite 8.3**, **Tailwind CSS v4** | Modular Single Page Application (SPA) with role-based routing, glassmorphism UI, and real-time state sync. |
| **Data Visualization** | **Recharts**, **Lucide React Icons** | Dynamic charts (Area, Bar, Line, Pie) displaying telemetry, KPIs, and monthly waste diversion trends. |
| **Machine Learning** | **LightGBM**, **XGBoost**, **Scikit-Learn**, **Pandas**, **NumPy** | Predictive demand forecasting (Genpact Food Demand Dataset) and multi-variable waste risk estimation. |
| **Computer Vision** | **EfficientNet-B0**, **ONNX Runtime / PyTorch**, **OpenCV**, **Pillow** | Multi-class visual freshness scoring, surface blemish detection, and shelf-life clearance. |
| **IoT & Edge Simulation** | **Python AsyncIO**, **MQTT (Paho-MQTT)** | Telemetry simulator generating temperature, humidity, gas concentration, and power readings. |
| **Sustainability Engine** | **Poore & Nemecek (Science 2018)** LCA matrix | Scientific life-cycle impact calculator for greenhouse gases ($kg\ CO_2e$), water ($L$), and land use. |
| **Testing & Quality** | **Pytest**, **FastAPI TestClient**, **HTTPX** | Comprehensive automated regression suite containing 118 test cases and 70 end-to-end audit assertions. |

---

## 4. Role-Based Access Control (RBAC) Matrix

The system implements strict, server-enforced role authorization via `require_roles(...)` dependencies:

| Endpoint Group | `SUPER_ADMIN` | `KITCHEN_MANAGER` | `QUALITY_INSPECTOR` | `LOGISTICS_COORDINATOR` | `NGO_REP` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Executive Analytics** (`/analytics/executive-stats`) | ✅ Full Access | ❌ 403 Forbidden | ❌ 403 Forbidden | ❌ 403 Forbidden | ❌ 403 Forbidden |
| **Monthly Trends & ESG Audit** (`/analytics/monthly-trend`) | ✅ Full Access | ❌ 403 Forbidden | ❌ 403 Forbidden | ❌ 403 Forbidden | ❌ 403 Forbidden |
| **Inventory & Batch Logging** (`/inventory/batches`) | ✅ Full Access | ✅ Full Access | ❌ 403 Forbidden | ❌ 403 Forbidden | ❌ 403 Forbidden |
| **Production Schedules** (`/production/schedules`) | ✅ Full Access | ✅ Full Access | ❌ 403 Forbidden | ❌ 403 Forbidden | ❌ 403 Forbidden |
| **Demand Predictions** (`/demand/predict`) | ✅ Full Access | ✅ Full Access | ❌ 403 Forbidden | ❌ 403 Forbidden | ❌ 403 Forbidden |
| **CV Freshness Scanning** (`/quality/scan`) | ✅ Full Access | ✅ Full Access | ✅ Full Access | ❌ 403 Forbidden | ❌ 403 Forbidden |
| **Logistics Routes & Dispatch** (`/logistics/routes`) | ✅ Full Access | ✅ Read Only | ❌ 403 Forbidden | ✅ Full Access | ❌ 403 Forbidden |
| **Surplus Discovery & Claim** (`/redistribution/surplus`) | ✅ Full Access | ✅ Post Surplus | ❌ 403 Forbidden | ❌ 403 Forbidden | ✅ Claim Surplus |
| **Sustainability Metrics** (`/sustainability/metrics`) | ✅ Full Access | ✅ Read Only | ✅ Read Only | ✅ Read Only | ✅ Read Only |

---

## 5. Machine Learning, Computer Vision & Scientific Algorithms

### 5.1 LightGBM Predictive Demand Engine
- **Input Features**: Day of week, academic calendar cycle (exam week, holiday), historical headcount, weather indicators, meal type (breakfast, lunch, dinner).
- **Objective**: Minimize overproduction by computing meal quantities with 90%+ confidence intervals.
- **Fail-Safe Design**: When the dedicated ML microservice (`localhost:8001`) is offline, the backend executes an integrated heuristic fallback algorithm based on recent rolling historical averages.

### 5.2 EfficientNet-B0 Computer Vision Freshness Classifier
- **Image Input**: Multi-angle RGB imagery of raw or cooked food batches.
- **Analysis**: Detects surface discoloration, moisture loss, and bacterial colonization.
- **Output Schema**:
  - `freshness_score`: Continuous metric from `0.0` to `100.0`.
  - `predicted_category`: Enum (`FRESH`, `MARGINAL`, `SPOILED`).
  - `recommended_action`: (`IMMEDIATE_USE`, `SAFE_REDISTRIBUTE`, `COMPOST_DISPOSAL`).
  - `remaining_shelf_life_hours`: Hours before critical quality decay.
  - `simulated`: Boolean flag indicating whether hardware inference or software heuristic was used.

### 5.3 Poore & Nemecek Environmental Life-Cycle Accounting
Food waste impacts are computed using empirical emission factors derived from Poore & Nemecek (*Science*, 2018):
- **Cereals / Grains**: $1.60\ kg\ CO_2e / kg$, $1,644\ L\ water / kg$
- **Vegetables**: $0.53\ kg\ CO_2e / kg$, $322\ L\ water / kg$
- **Dairy / Paneer**: $8.90\ kg\ CO_2e / kg$, $3,178\ L\ water / kg$
- **Meat / Poultry**: $12.30\ kg\ CO_2e / kg$, $4,325\ L\ water / kg$
- **Methane Conversion**: Every kilogram of organic matter diverted from anaerobic landfill decomposition eliminates approximately $0.45\ kg\ CH_4$ equivalent.

---

## 6. Database Entity-Relationship Topology

The platform schema consists of **23 relational tables** managed through SQLAlchemy:
1. `organizations`: Multi-tenant institutional cluster governance.
2. `users`: Identity, authentication credentials, and role assignments.
3. `kitchens`: Physical dining and preparation facilities.
4. `food_items`: Master catalog of ingredients, allergens, and shelf-life baselines.
5. `inventory`: Aggregated stock levels per kitchen.
6. `inventory_batches`: Per-lot tracking with barcode/QR, preparation timestamp, and expiry.
7. `production_schedules`: Planned daily meal outputs and actual prep adjustments.
8. `demand_predictions`: Stored AI forecasts against actual footfall for continuous training.
9. `waste_logs`: Granular disposal records categorized by cause (preparation, plate, spoiled).
10. `quality_inspections`: CV scan records, freshness scores, and inspector sign-offs.
11. `sensor_readings`: High-frequency IoT telemetry (temperature, humidity, ammonia/methane, kWh).
12. `energy_logs`: Daily facility power, water, and gas consumption metrics.
13. `maintenance_tasks`: Preventive and corrective equipment work orders.
14. `machine_events`: Sensor-triggered machinery vibration and anomaly events.
15. `ngo_partners`: Vetted charity profiles, verified vehicle fleets, and capacity.
16. `redistribution_requests`: Available surplus lots flagged for donation.
17. `redistribution_claims`: Claim transactions binding an NGO partner to a surplus lot.
18. `routes`: Optimized delivery legs and dispatch schedules.
19. `delivery_stops`: Waypoints with arrival windows, latitude/longitude, and completion state.
20. `sustainability_metrics`: Aggregated environmental savings ($CO_2e$, water, meals).
21. `alerts`: System notifications across hazard warnings, expiring batches, and claims.
22. `audit_logs`: Immutable trail of administrative actions for enterprise security.
23. `esg_reports`: Generated compliance records for BRSR and ISO 14001 audits.

---

## 7. Audit Findings, Vulnerabilities Identified & Remediations

During the Phase 1 through Phase 7 audits, the codebase was systematically inspected and hardened. The table below details every identified vulnerability and its resolution:

| Audit ID | Severity | Component | Defect / Vulnerability Identified | Remediation Implemented | Status |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **SEC-01** | High | Auth Rate Limiter | Auth endpoints vulnerable to brute-force attacks in test/development environments. | Implemented sliding-window rate limiter (100 req/min dev, 10 req/min prod). | ✅ Verified |
| **SEC-02** | High | Logistics Router | `GET /routes` endpoint used `get_current_user` instead of `require_roles`, exposing fleet routes to unprivileged roles. | Replaced dependency with `require_roles(["LOGISTICS_COORDINATOR", "SUPER_ADMIN", "KITCHEN_MANAGER"])`. | ✅ Verified |
| **DAT-01** | Medium | Quality Router | CV scan responses did not indicate whether the inference was simulated or executed on GPU/ONNX. | Added `simulated: bool` and `simulation_notice: str` to `QualityScanResponse` schema. | ✅ Verified |
| **DAT-02** | Medium | Sustainability Router | `EsgAuditReportOut` schema omitted `total_food_saved_kg`, causing incomplete ESG certificate exports. | Added alias and schema field ensuring complete ESG payload download. | ✅ Verified |
| **DAT-03** | Medium | Frontend Fallback | Offline fallback state returned hardcoded demo figures (14,250 kg saved) when the backend was unreachable. | Replaced fabricated values with honest zero-state indicators and connectivity alerts. | ✅ Verified |
| **DEV-01** | Medium | Backend Launcher | Running `uvicorn main:app` inside `backend/` failed with `ModuleNotFoundError: No module named 'backend'`. | Added dynamic project root resolution to `sys.path` in `main.py` and `config.py`. | ✅ Verified |
| **DEV-02** | Low | Database Path | Relative SQLite path `sqlite:///./reserve_ai.db` created separate databases when launched from different directories. | Updated `database.py` to always resolve relative SQLite paths against the workspace root. | ✅ Verified |

---

## 8. Verification & Test Suite Results

The codebase underwent automated testing across both unit and end-to-end integration levels:

```text
============================== Test Execution Summary ==============================
Suite: pytest tests/ --tb=short -q
Total Test Cases: 118
Passed: 118
Failed: 0
Execution Time: 7.51 seconds
Coverage: Auth, RBAC, Demand, Inventory, Logistics, Quality, Waste, Sustainability

=========================== P7 Deep Verification Summary ===========================
Script: p7_verify.py (Multi-Batch Role & Workflow Audit)
Total Checks: 70
Passed: 70
Failed: 0
Batches Verified:
  - Batch 1: User Discovery across all 5 roles (5/5 PASS)
  - Batch 2: Auth Contracts (401/403/tokens/rate-limits) (10/10 PASS)
  - Batch 3: Role Endpoint RBAC (12/12 PASS)
  - Batch 4: End-to-End Circular Workflow (Prep -> Scan -> Surplus -> Claim -> Route) (7/7 PASS)
  - Batch 5: Analytics & ESG Scientific Integrity (8/8 PASS)
  - Batch 6: Resilience & Fail-Safe Fallbacks (28/28 PASS)
```

---

## 9. SIH 2026 Evaluation & Demonstration Readiness

| SIH Evaluation Parameter | Platform Capability & Evidence |
| :--- | :--- |
| **Innovation & Novelty** | Integrates predictive AI (LightGBM) with physical verification (Computer Vision) and real-time logistics (OR-Tools) into a unified circular supply chain. |
| **Technical Complexity** | Multi-tiered microservice architecture supporting WebSockets, IoT ingestion, machine learning inference, and 23-table relational schema. |
| **Data Authenticity** | Zero fabricated figures; offline modes display transparent zero-states; simulation notices are declared on heuristic CV scans. |
| **Security & Compliance** | Role-based access control (RBAC) enforced on both backend routes and frontend UI; Argon2 password hashing; JWT authentication. |
| **Measurable Impact** | Direct calculation of carbon avoidance ($kg\ CO_2e$) and water conservation ($L$) aligned with international life-cycle assessment standards. |
| **Deployment Readiness** | Containerized deployment via Docker Compose; instant local execution via `run_local.ps1` and `run_local.bat`. |

---
*Report certified and compiled by Antigravity AI Engineering Suite.*
