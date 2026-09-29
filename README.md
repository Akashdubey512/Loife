# reServe AI 🌿
### AI-Powered Smart Food Waste Reduction and Sustainable Redistribution Platform
**Smart India Hackathon (SIH 2026) Enterprise Edition**

![reServe AI System Architecture](https://img.shields.io/badge/Platform-Enterprise%20SaaS-10b981?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/Frontend-React%2019%20%2B%20TS-61DAFB?style=for-the-badge&logo=react)
![Tailwind](https://img.shields.io/badge/Styling-Tailwind%20v4-38B2AC?style=for-the-badge&logo=tailwind-css)
![Docker](https://img.shields.io/badge/Containers-Docker%20Compose-2496ED?style=for-the-badge&logo=docker)

---

## 🌟 1. Project Overview & Problem Statement

Across the global food supply chain, over one-third of all food produced is lost or discarded, squandering arable land, fresh water, and energy while driving 8-10% of global greenhouse gas emissions. In India, institutional kitchens (university messes, corporate tech campuses, hospital catering, and central food processing units) face acute friction between demand volatility, bulk prep overproduction, and perishable shelf-life decay.

**reServe AI** is a production-grade, enterprise SaaS ecosystem that transforms linear food waste into an intelligent, closed-loop circular redistribution network.

### Core Capabilities:
1. **LightGBM Demand Forecasting**: Sub-meal slot predictive demand estimation factoring academic calendars, footfall surges, weather, and price elasticity.
2. **Computer Vision Freshness Scoring**: Convolutional Neural Network (EfficientNet-B0) assessing surface oxidation, cellular softening, and spoilage to assign remaining shelf life and safety clearance.
3. **IoT Cold-Chain Storage Monitoring**: Real-time environmental telemetry (Temperature, Humidity, Methane/Ammonia gas, Power kWh) with sub-second threshold breach hazard alerts.
4. **Autonomous NGO Redistribution Engine**: Multi-factor pairing of safe surplus with nearby verified food banks (Robin Hood Army, Feeding India) factoring distance, capacity, urgency, and cold-storage compatibility.
5. **Smart Logistics & Route Optimization**: Capacitated Vehicle Routing Problem (CVRPTW) solving optimal multi-stop routes using Google OR-Tools.
6. **Poore & Nemecek ESG Sustainability Accounting**: Life-cycle assessment of CO2e avoided, virtual water conserved, and automated Scope 3 compliance report generation.

---

## 🏗️ 2. Repository Structure

```
reServeAi/
├── .github/workflows/          # GitHub Actions CI/CD test and build pipelines
├── backend/                    # Modular FastAPI Enterprise Service
│   ├── auth/                   # JWT OAuth2 authentication & Argon2 hashing
│   ├── users/                  # User identity & RBAC permission controls
│   ├── organizations/          # Multi-tenant institutional cluster governance
│   ├── kitchens/               # Kitchen facilities & live operational overviews
│   ├── inventory/              # Inventory catalog & batch expiry tracking
│   ├── production/             # Daily prep schedules & batch adjustments
│   ├── demand/                 # Predictive demand forecast endpoints
│   ├── waste/                  # Waste event tracking & XGBoost waste prediction
│   ├── quality/                # Computer Vision food freshness scan API
│   ├── sensors/                # IoT sensor ingestion & threshold breach alerts
│   ├── energy/                 # Power (kWh) & water efficiency telemetry
│   ├── maintenance/            # Predictive equipment maintenance (AI4I 2020)
│   ├── redistribution/         # Multi-factor NGO matching & surplus auction
│   ├── logistics/              # Vehicle route optimization (OR-Tools)
│   ├── sustainability/         # Poore & Nemecek lifecycle impact accounting
│   ├── notifications/          # Real-time WebSockets & emergency alerts
│   ├── analytics/              # Executive KPI analytics & monthly trends
│   ├── core/                   # DB connection (PostgreSQL/SQLite), settings, JWT
│   ├── models/                 # 23 relational SQLAlchemy entities
│   ├── schemas/                # Pydantic v2 validation contracts
│   └── services/               # Realistic institutional database seeder
├── frontend/                   # React 19 + TypeScript + Tailwind CSS Console
│   ├── src/
│   │   ├── dashboards/         # 6 Interactive Enterprise Dashboards
│   │   │   ├── ExecutiveDashboard.tsx      # High-level KPIs & monthly trends
│   │   │   ├── KitchenDashboard.tsx        # Shift demand & expiring batches
│   │   │   ├── QualityDashboard.tsx        # CV freshness scan & shelf-life
│   │   │   ├── RedistributionDashboard.tsx # NGO matching & surplus dispatch
│   │   │   ├── LogisticsDashboard.tsx      # Live GPS map simulation & routes
│   │   │   └── SustainabilityDashboard.tsx # ESG certificate & environmental metrics
│   │   ├── components/         # Navbar, Sidebar, StatCard, alerts
│   │   ├── services/           # Axios REST client with fallback resiliency
│   │   └── types/              # Comprehensive TypeScript interfaces
├── ml/                         # AI & Machine Learning Pipeline
│   ├── demand_forecast.py      # LightGBM pipeline (Genpact Food Demand dataset)
│   ├── waste_predictor.py      # Multi-variable food waste risk classifier
│   ├── sustainability_engine.py# Poore & Nemecek lifecycle calculation engine
│   ├── predictive_maintenance.py# AI4I 2020 predictive maintenance classifier
│   ├── dvc.yaml                # DVC data and model pipeline tracking
│   └── service.py              # Standalone ML microservice (Port 8001)
├── cv/                         # Computer Vision Intelligence
│   └── freshness_classifier.py # EfficientNet-B0 freshness & shelf life estimator
├── iot/                        # IoT Telemetry & Edge Simulator
│   └── simulator.py            # ESP32 sensory batch streamer (Temp, Humidity, Gas)
├── logistics/                  # Vehicle Routing Engine
│   └── optimizer.py            # Capacitated Vehicle Routing Problem (CVRPTW) solver
├── deployment/                 # Production Docker & Cloud Deployments
│   ├── docker-compose.yml      # Orchestrates Postgres, Redis, Backend, ML, Frontend
│   ├── Dockerfile.backend      # Python 3.11 FastAPI container
│   ├── Dockerfile.frontend     # Multi-stage Nginx production container
│   ├── Dockerfile.ml           # Dedicated machine learning service container
│   └── nginx.conf              # Reverse proxy & WebSocket routing
├── docs/                       # Technical Specifications & SIH Documentation
│   ├── SYSTEM_ARCHITECTURE.md  # End-to-end data flow & component topology
│   ├── DATABASE_SCHEMA.md      # 23-table relational schema & ERD
│   ├── API_CONTRACT.md         # Complete REST & WebSocket API specification
│   └── DEVELOPMENT_ROADMAP.md  # Phase-wise milestones & SIH judging criteria
└── tests/                      # Pytest automated API testing suite
```

---

## 🚀 3. Quick Start Guide

### Option A: Docker Compose (Production Setup)
```bash
# Clone the repository
git clone https://github.com/reServeAI/reServeAi.git
cd reServeAi

# Start all microservices in background
docker compose up -d --build
```
- **Frontend Dashboard**: `http://localhost:3000`
- **Backend API Docs (Swagger)**: `http://localhost:8000/api/v1/docs`
- **ML Microservice**: `http://localhost:8001`

### Option B: Local Development (Without Docker)

#### 1. Backend Setup:
```bash
# From workspace root
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

#### 2. Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🔑 4. Demo Evaluation Accounts

Pre-seeded institutional accounts for instant demonstration across all role-based personas:

| Role | Email | Password | Access Scope |
|---|---|---|---|
| **Super Admin** | `admin@reserve.ai` | `Admin@123` | Platform-wide governance, cross-org analytics, user management |
| **Kitchen Manager** | `kitchen.lead@techcorp.com` | `Kitchen@123` | Demand planning, prep schedules, inventory batch expiry |
| **Quality Inspector** | `inspector@reserve.ai` | `Quality@123` | CV image scans, cold-chain checks, certified sign-off |
| **Logistics Coordinator**| `logistics@reserve.ai` | `Logistics@123` | OR-Tools CVRPTW solver, route dispatch, OTP delivery verification |
| **NGO Representative** | `contact@robinhoodarmy.com` | `NGO@123` | Surplus matching, 1-click claims, meal acceptance |

---

## 🧪 5. Automated Testing Suite

All 26 automated integration tests pass with zero errors:

```bash
# Execute full API & workflow test suite
pytest -v tests/test_api.py
```

### Test Coverage Highlights:
- **Authentication & RBAC**: JWT login, token invalidation, role-based boundary controls (`test_rbac_authorization_restrictions`).
- **Multi-Tenant Isolation**: Cross-organization prevention with `403 Forbidden` (`test_cross_organization_tenant_isolation`).
- **Workflow A (Demand)**: 7-day historical consumption lags, inventory netting, and persistence (`test_demand_prediction_persistence`).
- **Workflow B (Waste)**: Waste risk prediction with high-severity alert triggering (`test_waste_prediction_alert_and_persistence`).
- **Workflow C (Quality)**: CV inference, sensor cold-chain check, and certified human verification (`test_quality_inference_and_human_verification`).
- **Workflow D (Redistribution & Logistics)**: Google OR-Tools CVRPTW, duplicate claim prevention (409 Conflict), and OTP Proof of Delivery (`test_cvrptw_route_optimization_and_duplicate_prevention`, `test_duplicate_redistribution_prevention`, `test_delivery_confirmation_via_otp`).
- **Workflow E (ESG Accounting)**: Physical recovery vs pipeline potential, and Scope 3 Audit Report generation (`test_sustainability_esg_audit_generation`).
- **IoT Resilience**: Sensor threshold breach detection with automatic hazard creation (`test_sensor_threshold_hazard_alert`).

---

## 📚 6. Documentation Suite

Comprehensive architecture, API, and engineering specifications:
- [Production Readiness Audit](docs/PRODUCTION_READINESS_AUDIT.md) — 8 findings remediated, test matrix, and audit closure.
- [System Architecture](docs/ARCHITECTURE.md) — Multi-tier architecture, data flow diagrams, and component interactions.
- [REST & WebSocket API Guide](docs/API_DOCUMENTATION.md) — Complete endpoint schemas, authentication, and error codes.
- [Relational Database Schema](docs/DATABASE_SCHEMA.md) — 23 core entities, ERD, indexes, concurrency locking, and PITR.
- [AI/ML & CV Model Documentation](docs/AI_MODEL_DOCUMENTATION.md) — LightGBM, EfficientNet-B0, OR-Tools, and ESG equations.
- [Production Deployment Guide](docs/DEPLOYMENT_GUIDE.md) — Docker Compose, Nginx, SSL, environment variables, and troubleshooting.
- [Automated Testing Specification](docs/TESTING.md) — Test matrix, fixtures, execution commands, and CI/CD automation.

---

## 📊 7. Key Scientific & Algorithmic Baselines

1. **Demand Forecasting**: Evaluated against the **Genpact Food Demand Forecasting** dataset with lag features ($t-1, t-7$), 7-day rolling means, and promotion price elasticity.
2. **Quality Assessment**: Evaluated against the **Kaggle Fresh and Rotten Fruits & Vegetables** dataset using transfer learning on **EfficientNet-B0**.
3. **Predictive Maintenance**: Tested against the **UC Irvine AI4I 2020 Predictive Maintenance Dataset** incorporating physical boundary equations for Heat Dissipation (HDF), Power (PWF), and Overstrain (OSF) failures.
4. **Sustainability Multipliers**: Derived from **Poore & Nemecek (Science 2018)** and **Our World in Data (OWID)** lifecycle assessment footprints.

---

## 🏆 8. SIH 2026 Competitive Edge
- **Zero Mock UI**: Fully functional, dynamic dark glassmorphism console with live simulations, real API mutations, and instant feedback.
- **Enterprise-Grade Architecture**: 23 relational database entities, row-level locking, and unified WebSocket telemetry.
- **Academic & Regulatory Rigor**: Differentiates real dataset training dynamics from high-density simulation fixtures; enforces independent food safety beyond optical CV.
