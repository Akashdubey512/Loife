# reServe AI — AI/ML Model Architecture & Reliability Documentation

## 1. Overview of AI/ML Systems

reServe AI deploys four core analytical and machine learning subsystems:
1. **Demand Forecasting Engine** (`ml/demand_forecast.py`): LightGBM / Pure-Python hybrid for shift-level ingredient and meal demand prediction.
2. **Surplus & Waste Prediction Model** (`ml/waste_predictor.py`): XGBoost surplus risk classifier calculating waste probabilities and root causes.
3. **Computer Vision Freshness Classifier** (`cv/freshness_classifier.py`): EfficientNet-B0 convolutional feature extractor with heuristic spectral degradation scoring.
4. **Capacitated Vehicle Routing Optimizer** (`logistics/optimizer.py`): Google OR-Tools routing engine solving multi-stop time-constrained food deliveries.

---

## 2. Demand Forecasting Engine

- **Model Type**: Gradient Boosted Decision Trees (LightGBM v4.x) with pure-Python resilient mathematical fallback.
- **Dataset Provenance**: Trained on the Genpact Food Demand Forecasting benchmark (51 weeks of multi-center institutional catering meal sales).
- **Features Used**:
  - `center_id`, `meal_id`, `day_of_week`, `calendar_month`
  - `base_price`, `checkout_price`, `discount_rate`
  - `lag_7_days`, `lag_14_days`, `rolling_mean_7_days`
  - Footfall surges and academic calendar schedule indicators
- **Input Validation**:
  - Missing lags are imputed using moving exponential averages.
  - Negative quantities and checkout prices > base prices are clamped with error bounds.
- **Latency & Performance**:
  - Inference Latency: **< 15ms** per kitchen query.
  - Evaluation Metric: RMSE benchmarked against naive 7-day rolling average (28.4% improvement on historical Genpact holdout).
- **Graceful Fallback**: If compiled C-extensions are blocked by OS security policies (e.g. Windows WDAC/AppLocker), the pure-Python mathematical engine takes over seamlessly without downtime.

---

## 3. Surplus & Waste Risk Classifier

- **Model Type**: Extreme Gradient Boosting (XGBoost v2.x).
- **Task**: Multi-class surplus risk classification (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
- **Features Used**:
  - `scheduled_production_kg`
  - `forecasted_demand_kg`
  - `imminent_expiry_inventory_kg` (<14 hours remaining)
  - Historical kitchen prep accuracy index
- **Output Contracts**:
  - `expected_waste_kg`: Estimated surplus mass in kg.
  - `surplus_risk_probability`: Probability (0.0 to 1.0) of overproduction.
  - `predicted_root_cause`: Categorized failure cause (e.g., `UNCONSUMED_HELD_FOOD`, `FOOTFALL_DEVIATION`).
  - `prevention_recommendation`: Actionable guidance for the kitchen crew.
- **Safety Threshold**: When `surplus_risk_probability >= 0.20`, a system `Alert` is automatically pushed to kitchen dashboards and logged in the operational audit trail.

---

## 4. Computer Vision Freshness & Shelf-Life Classifier

- **Model Architecture**: EfficientNet-B0 (pretrained on ImageNet, fine-tuned on Kaggle Fresh and Rotten Fruits & Vegetables Dataset).
- **Input Dimensions**: 3-channel RGB image tensor (224 x 224 x 3).
- **Class Outputs**: `FRESH`, `MODERATE`, `DEGRADING`, `ROTTEN`.
- **Confidence Calibration**: Softmax temperature-scaled probability distribution.
- **Multi-Factor Safety Governance**:
  - **FSSAI Compliance Rule**: Optical classification is *never* treated as the sole certification of food safety.
  - If a batch has passed its expiration timestamp, it is classified as `HAZARD_DISCARD` regardless of visual appearance.
  - If cold-chain telemetry detected a temperature spike (> 8°C) within the preceding 24 hours, the disposition is automatically downgraded to `PROCESS_IMMEDIATELY` or flagged for lab review.
  - All redistribution batches require certified **Human Inspector Verification Sign-Off** via `POST /api/v1/quality/scans/{id}/verify`.

---

## 5. Operations Research Vehicle Routing (CVRPTW)

- **Engine**: Google Operations Research (OR-Tools) Vehicle Routing Solver.
- **Objective Function**: Minimize total fleet transport distance while satisfying:
  1. **Vehicle Capacity**: Vehicle load must never exceed rated payload (default: 500.0 kg).
  2. **Shelf-Life Urgency (Time Windows)**: Deliveries with shorter shelf-life urgency are sequenced first.
  3. **Multi-Stop Drop Sequence**: Automated pickup from commissary hub followed by sequential distribution drops.
- **Haversine Matrix**: Pre-computes great-circle distances between kitchen depots and geocoded NGO centers.

---

## 6. ESG Environmental Footprint Multipliers

Environmental offsets are computed using peer-reviewed lifecycle assessment data from **Poore & Nemecek (Science 2018)**:

| Category | CO₂e / kg | Water (L) / kg | Land (m²) / kg | Institutional Value (₹/kg) |
|---|---|---|---|---|
| **Cooked Meals** | 2.50 kg | 500.0 L | 2.00 m² | ₹110 |
| **Vegetables & Produce** | 0.50 kg | 322.0 L | 0.40 m² | ₹45 |
| **Dairy & Paneer** | 3.20 kg | 628.0 L | 4.50 m² | ₹180 |
| **Bakery & Bread** | 1.60 kg | 1100.0 L | 1.80 m² | ₹65 |
| **Grains & Rice** | 1.40 kg | 1200.0 L | 2.10 m² | ₹55 |

- **Scope 3 Distinction**: Physical verified deliveries (`DELIVERED`) are recorded as **Measured Savings**. Batches in matching or transit are reported as **Pipeline Potential**.
