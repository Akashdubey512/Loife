# ReServeAI — System Architecture

## 1. High-Level Architecture
ReServeAI is an enterprise-grade AI-powered food surplus redistribution, cold-chain assurance, and waste reduction platform. The architecture separates presentation, API orchestration, relational transactional storage, machine learning inference engines, and logistics optimization.

```
                      +-----------------------------+
                      |   Client Web Application    |
                      |   React 18 + Vite + TS      |
                      +--------------+--------------+
                                     |
                          HTTPS / WSS / REST API
                                     |
                      +--------------v--------------+
                      |  Reverse Proxy & Gateways   |
                      |     Nginx (TLS / Reverse)   |
                      +--------------+--------------+
                                     |
            +------------------------+------------------------+
            |                                                 |
+-----------v-----------------------+             +-----------v-----------------------+
|  FastAPI Backend Core Service     |             |  Telemetry & WebSockets           |
|  - Auth & RBAC (PBKDF2 / HS256)   |             |  - Telemetry Broadcaster          |
|  - 17 Domain Feature Routers      |             |  - Live Cold-Chain Alerts         |
|  - Rate Limiter (IP sliding-win)  |             +-----------------------------------+
|  - SQLAlchemy 2.0 ORM             |
+-----------+-----------------------+
            |
            +------------------------+------------------------+
            |                        |                        |
+-----------v-----------+  +---------v-----------+  +---------v-------------------------+
| Relational Storage    |  | In-Memory Cache     |  | AI / ML & Optimization Engines    |
| - PostgreSQL (Prod)   |  | - Redis 7 (Pub/Sub) |  | 1. Demand Forecaster (LightGBM)   |
| - SQLite 3 (Dev/UAT)  |  +---------------------+  | 2. Predictive Maintenance (LGBM)  |
| 16 Normalized Tables  |                           | 3. Energy Forecaster (LightGBM)   |
| ACID Transactions     |                           | 4. E-Nose Beef Classifier (LGBM)  |
+-----------------------+                           | 5. Fruit CV (Spectral Simulated)  |
                                                    | 6. Waste Engine (Rule-based)      |
                                                    | 7. Sustainability LCA (Poore)     |
                                                    | 8. Route Optimizer (Clarke-Wright)|
                                                    +-----------------------------------+
```

---

## 2. Core Subsystems

### A. Authentication & Multi-Tenant RBAC
- **Password Security:** PBKDF2 with HMAC-SHA256, 100,000 rounds, cryptographic salts.
- **JWT Authorization:** HS256 signed access tokens with strict expiration and subject binding.
- **Role Enforcement:** Strict server-side RBAC dependencies (`require_roles`) guarding every sensitive endpoint across 10 defined platform roles.
- **Tenant Isolation:** Foreign key tenant checks guarantee organizational boundary isolation.

### B. Machine Learning Engine Tier
- **Demand Forecasting:** LightGBM regressor predicting meal requirements from day of week, pricing, promotions, and historical demand.
- **Predictive Maintenance:** LightGBM classifier predicting equipment failure risks across air temp, rotational speed, torque, and tool wear.
- **Energy Prediction:** LightGBM regressor forecasting kitchen appliance Wh load.
- **E-Nose Sensor:** LightGBM 4-class classifier evaluated on Mendeley E-Nose dataset (**Strictly scoped to Beef Quality**).
- **Fruit Freshness CV:** Spectral-spatial colorimetric simulation engine (`spectral-spatial-v2.1-SIMULATED`). Mandatory human verification required.
- **Waste Predictor:** Rule-based fallback model (`rule-based-v1.0`) pending accumulation of real kitchen waste production events.
- **Sustainability LCA:** Poore & Nemecek (2018) empirical lifecycle assessment matrix covering 42 food products.
- **Logistics Route Optimizer:** Clarke-Wright Savings with Intra-Route 2-Opt local search heuristics.

---

## 3. Data Integrity & Resilience
- Transactions are managed via SQLAlchemy scoped sessions with explicit commits and rollback handlers.
- Multi-tier health endpoints (`/health`, `/health/live`, `/health/ready`) provide container orchestrators with accurate liveness and dependency readiness statuses.
