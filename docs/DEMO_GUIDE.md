# ReServeAI — Practical Demonstration Guide

## 1. Pre-Demo Checklist

Before initiating an evaluation or live stakeholder presentation, verify the following:
- [ ] **Backend Running:** `uvicorn backend.main:app --port 8000` is active.
- [ ] **Frontend Running:** Vite development server is active at `http://localhost:3000` (or `http://localhost:5173`).
- [ ] **Database Available:** `reserve_ai.db` (SQLite) or PostgreSQL container is responsive.
- [ ] **Environment Configured:** `.env` exists with valid configuration parameters.
- [ ] **Demo Accounts Verified:** Credentials tested for Admin, Kitchen Manager, Quality Inspector, Logistics Coordinator, and NGO Rep.
- [ ] **Health Probe Check:** `curl http://localhost:8000/health/live` returns HTTP 200 `ALIVE`.
- [ ] **Readiness Probe Check:** `curl http://localhost:8000/health/ready` returns HTTP 200 `READY`.

---

## 2. Step-by-Step Demonstration Flow

### Step 1: Authentication & Role-Based Login
- **What to do:** Open the application homepage, click **Login**, enter:
  - Email: `kitchen@reserveai.com`
  - Password: `Kitchen@1234`
- **What appears:** Redirects to the Kitchen Operations Dashboard with the chef persona loaded.
- **Concept demonstrated:** PBKDF2 (100k rounds) hashing, JWT issuance, and role-based redirect.

### Step 2: Kitchen Dashboard & Shift Overview
- **What to do:** Inspect the top KPI summary cards and active batch lists.
- **What appears:** Real-time production metrics, scheduled shifts, expiring inventory warnings (<14 hours), and net production recommendations.
- **Concept demonstrated:** Prevention of kitchen overproduction through inventory netting.

### Step 3: Kitchen Inventory & Demand Forecast
- **What to do:** Navigate to the **Demand & Inventory** tab.
- **What appears:** LightGBM demand forecast graph displaying expected demand in kilograms with confidence intervals.
- **Concept demonstrated:** Integration of `demand-lgbm-v1.0` trained on 50,000 real Genpact order events.

### Step 4: Surplus Food Creation & Posting
- **What to do:** Select an inventory batch nearing end-of-shift, enter available quantity (e.g. 25 kg), and click **Register Surplus Lot**.
- **What appears:** A new surplus request is posted with status `POSTED` and calculated shelf-life urgency window.
- **Concept demonstrated:** Transforming kitchen waste into circular redistribution opportunities.

### Step 5: Food Quality Inspection & Fruit CV Simulation
- **What to do:** Log out and log in as `quality@reserveai.com` (`Quality@1234`). Navigate to **Quality Scanner**, upload a sample produce image, and click **Analyze Freshness**.
- **What appears:** The freshness card renders a freshness score (e.g., 98.5% FRESH), but explicitly flags:
  - `Simulation Mode: True`
  - `Status: PENDING_HUMAN_VERIFICATION`
  - Warning banner: *"Simulated Colorimetric CV — Certified human verification is mandatory before redistribution."*
- **What to do next:** As the inspector, click **Verify & Sign Off**.
- **Concept demonstrated:** Scientific honesty: Fruit CV is simulated (`spectral-spatial-v2.1-SIMULATED`), enforcing human oversight rather than fabricating autonomous food safety clearance.

### Step 6: NGO Surplus Discovery & Reservation
- **What to do:** Log out and log in as `ngo@reserveai.com` (`NGO@1234`). Navigate to **Surplus Feed**.
- **What appears:** The newly verified surplus lot appears in the NGO discovery list with haversine distance, meal quantity, and temperature safety clearance. Click **Claim Surplus**.
- **What appears:** Status updates to `CLAIMED` with single-claim database locks preventing race conditions or double-claims.
- **Concept demonstrated:** Autonomous multi-factor NGO matching with strict concurrency control.

### Step 7: Logistics Route Optimization & Dispatch
- **What to do:** Log out and log in as `logistics@reserveai.com` (`Logistics@1234`). Navigate to **Fleet & Routing**, select pending stops, and click **Optimize Dispatch Route**.
- **What appears:** The route visualizer plots the optimal multi-stop sequence, displaying total distance in km and vehicle capacity utilization.
- **Concept demonstrated:** Clarke-Wright Savings with Intra-Route 2-Opt local search refinement (100% capacity feasibility).

### Step 8: Cold-Chain Telemetry & E-Nose Sensor Evaluation
- **What to do:** Navigate to **Sensory Telemetry**.
- **What appears:** Real-time temperature, humidity, and gas sensor channels. View the E-Nose meat evaluation widget displaying:
  - Quality Class: 1 (EXCELLENT) or 2 (GOOD)
  - Scope: **BEEF QUALITY ONLY** (Leakage-audited Mendeley dataset)
- **Concept demonstrated:** IoT environmental thresholding and scoped sensor ML.

### Step 9: Sustainability & Scope 3 ESG Metrics
- **What to do:** Log in as `admin@reserveai.com` (`Admin@1234`) and navigate to the **Sustainability Dashboard**.
- **What appears:** Dynamic cards displaying:
  - Total CO2e Avoided (kg)
  - Freshwater Conserved (Liters)
  - Equivalent Landfill Meals Diverted
  - Poore & Nemecek (2018) Science reference baseline citation.
- **Concept demonstrated:** Rigorous life-cycle sustainability accounting based on peer-reviewed environmental data.

### Step 10: Platform ML Status & Model Registry
- **What to do:** Navigate to **ML Model Status** (`/api/v1/ml/status`).
- **What appears:** A clean table listing all 8 platform engines:
  - Demand: `trained`
  - Maintenance: `trained`
  - Energy: `trained`
  - E-Nose: `trained (BEEF ONLY)`
  - Fruit CV: `simulated`
  - Waste: `fallback`
  - LCA: `active lookup`
  - Route Optimizer: `active optimization`
- **Concept demonstrated:** Absolute architectural consistency between code, runtime API, and user interface.

### Step 11: Production Health Probes
- **What to do:** Open browser tab to `http://localhost:8000/health/ready`.
- **What appears:** JSON payload confirming application readiness (`"status": "READY"`) with component-level statuses for database, authentication, and individual engines.
- **Concept demonstrated:** Container supervisor readiness integration.

---

## 3. Automated Demonstration Script
For an automated, non-interactive demonstration of all 11 core steps in the terminal:
```bash
python backend/scripts/demo_walkthrough.py
```
Outputs colored, formatted logs confirming execution of all workflows in under 2 seconds.
