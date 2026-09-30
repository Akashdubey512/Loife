# ReServeAI — Machine Learning & Optimization Registry

## 1. Engine Summary

| Engine | Version | Current State | Algorithm | Dataset / Source | Scope / Constraint |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Demand Forecasting** | `demand-lgbm-v1.0` | **Trained** | LightGBM Regressor | Genpact Food Demand (50k rows) | Meal-level demand forecasting |
| **Predictive Maintenance** | `maint-lgbm-v1.0` | **Trained** | LightGBM Classifier | AI4I 2020 Maintenance (10k rows) | Kitchen equipment failure detection |
| **Appliances Energy** | `energy-lgbm-v1.0` | **Trained** | LightGBM Regressor | Appliances Energy (19.7k rows) | Appliance energy load forecasting |
| **E-Nose Meat Quality** | `enose-lgbm-v1.0-leakage-audited` | **Trained** | LightGBM 4-Class | Mendeley E-Nose (20.8k rows) | **BEEF QUALITY ONLY** (Leakage-audited) |
| **Fruit CV Classifier** | `spectral-spatial-v2.1-SIMULATED` | **Simulated** | Spectral-Spatial | Mendeley Fruit Dataset (Blocked) | **FRUIT ONLY** (Human verification mandatory) |
| **Waste Classification** | `rule-based-v1.0` | **Fallback** | Rule-based | 0 Real Production Events | Fallback until production data logs |
| **Sustainability LCA** | `poore-nemecek-v2.0` | **Active Lookup** | Lookup Table | Poore & Nemecek (2018) Science | 42 agricultural products |
| **Route Optimizer** | `clarke-wright-2opt-v1.0` | **Active Optimization** | Clarke-Wright + 2-Opt | CVRPLIB Benchmark Instances | Combinatorial VRP Heuristic |

---

## 2. Details by Engine

### A. Demand Forecasting (`demand-lgbm-v1.0`)
- **Artifact:** `models/demand/demand_model.txt`, `metadata.json`
- **Trained:** Yes
- **Input Features:** `center_id`, `meal_id`, `checkout_price`, `base_price`, `has_emailer_promoter`, `has_homepage_featured`, `is_weekend`, `historical_avg_demand`
- **Output:** Continuous demand prediction in kilograms with confidence score.

### B. Predictive Maintenance (`maint-lgbm-v1.0`)
- **Artifact:** `models/maintenance/maintenance_model.txt`, `metadata.json`
- **Trained:** Yes
- **Input Features:** Air temperature, process temperature, rotational speed, torque, tool wear, machine type (L, M, H).
- **Output:** Failure probability and classification (`None`, `Heat Dissipation`, `Power Failure`, `Tool Wear`, `Overstrain`).

### C. Appliances Energy (`energy-lgbm-v1.0`)
- **Artifact:** `models/energy/energy_model.txt`, `metadata.json`
- **Trained:** Yes
- **Input Features:** Kitchen microclimate telemetry (T1-T9, RH1-RH9), weather observations (pressure, wind speed, visibility), time variables.
- **Output:** Expected energy consumption in Watt-hours.

### D. E-Nose Meat Quality (`enose-lgbm-v1.0-leakage-audited`)
- **Artifact:** `models/sensor/enose_model.txt`, `metadata.json`
- **Trained:** Yes (Leakage-audited: target TVC column removed from feature set).
- **Scope Restriction:** **STRICTLY BEEF QUALITY ONLY**. Must not be applied to chicken, pork, fish, dairy, or produce.
- **Classes:** 1: EXCELLENT, 2: GOOD, 3: ACCEPTABLE, 4: SPOILED.

### E. Fruit CV Classifier (`spectral-spatial-v2.1-SIMULATED`)
- **Status:** **SIMULATED**
- **Reason:** The legitimate Mendeley 2.79 GB multi-class fruit image archive cannot be downloaded or staged through the current host enterprise network.
- **Operational Requirement:** Any freshness prediction returned by this simulated pipeline carries `simulated=True`, `human_verified=False`, and requires explicit sign-off by a certified human quality inspector before food release.

### F. Waste Classification (`rule-based-v1.0`)
- **Status:** **FALLBACK**
- **Reason:** The production database currently contains 0 real historical waste records.
- **Operational Requirement:** Operates deterministically via cold-chain threshold heuristics and prep-volume estimation.
