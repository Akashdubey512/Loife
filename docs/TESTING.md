# reServe AI — Automated Testing & Quality Assurance Documentation

## 1. Test Suite Architecture

The automated test suite (`tests/test_api.py`) evaluates the complete end-to-end functionality of **reServe AI**, spanning:
- API endpoints & HTTP status codes
- Database CRUD & transactional integrity
- Concurrency locks & duplicate-claim prevention
- Multi-tenant isolation & RBAC enforcement
- Machine Learning pipelines (LightGBM, XGBoost, Poore & Nemecek LCA)
- Computer Vision food freshness & multi-factor food safety clearance
- IoT sensor threshold breaches & alert generation
- OR-Tools capacitated vehicle routing (CVRPTW)
- Digital Proof of Delivery (PoD) OTP verification

---

## 2. Test Inventory (26 Passing Tests)

| # | Test Name | Target Workflow | Description |
|---|---|---|---|
| 1 | `test_root_endpoint` | Health | Verifies service status is `OPERATIONAL`. |
| 2 | `test_executive_stats` | Executive KPI | Validates total food saved, waste reduction, and KPI bounds. |
| 3 | `test_auth_login` | Security | Validates credential authentication and JWT token issuance. |
| 4 | `test_auth_me_endpoint` | Identity | Validates `/auth/me` user claims and role retrieval. |
| 5 | `test_auth_invalid_credentials` | Security | Verifies that incorrect passwords return `401 Unauthorized`. |
| 6 | `test_demand_forecast` | Workflow A | Tests LightGBM/pure-Python demand forecast and production advice. |
| 7 | `test_demand_prediction_persistence` | Workflow A | Verifies predictions are persisted to the database. |
| 8 | `test_waste_prediction` | Workflow B | Tests XGBoost surplus prediction and prevention guidance. |
| 9 | `test_waste_prediction_alert_generation` | Workflow B | Verifies that risk >= 20% pushes a high-severity `Alert`. |
| 10 | `test_quality_scan_endpoint` | Workflow C | Validates image upload and EfficientNet-B0 inference. |
| 11 | `test_quality_human_verification_sign_off`| Workflow C | Verifies inspector sign-off clears lot for donation. |
| 12 | `test_surplus_and_matching` | Workflow D | Verifies active surplus lot retrieval for institutional kitchens. |
| 13 | `test_ngo_matching` | Workflow D | Tests multi-factor compatibility ranking of verified NGO partners. |
| 14 | `test_duplicate_redistribution_prevention`| Workflow D | Verifies concurrency lock returns `409 Conflict` on duplicate claim. |
| 15 | `test_logistics_route_optimization_endpoint`| Workflow D | Solves CVRPTW with OR-Tools, asserting distance and waypoints. |
| 16 | `test_delivery_status_advance_and_pod_confirmation`| Workflow D | Verifies OTP handover and creates Scope 3 sustainability credit. |
| 17 | `test_sustainability_summary` | Workflow E | Verifies Poore & Nemecek lifecycle multipliers and measured vs pipeline kg. |
| 18 | `test_sustainability_audit_report` | Workflow E | Generates Scope 3 ESG Audit Certificate with tree & car km offsets. |
| 19 | `test_sensor_reading_normal` | IoT Telemetry | Validates compliant cold-room temperature ingestion (3.4°C). |
| 20 | `test_sensor_reading_threshold_breached`| IoT Telemetry | Verifies 14.8°C spike triggers `is_threshold_breached: true`. |
| 21 | `test_cross_tenant_access_denial` | Security | Verifies Org 2 user querying Org 1 metrics receives `403 Forbidden`. |
| 22 | `test_ml_demand_engine` | ML Unit | Unit test for `demand_engine.predict` with 7-day historical lags. |
| 23 | `test_ml_waste_engine` | ML Unit | Unit test for `waste_engine.predict_waste`. |
| 24 | `test_ml_sustainability_engine` | ML Unit | Unit test for Poore & Nemecek lifecycle calculations. |
| 25 | `test_cv_freshness_pipeline` | CV Unit | Unit test for `cv_pipeline.infer` spectral degradation extractor. |
| 26 | `test_logistics_optimizer` | Logistics Unit| Unit test for `VehicleRoutingOptimizer` depot-and-stops solver. |

---

## 3. Running the Test Suite

### Execute Full Pytest Suite:
```bash
python -m pytest tests/test_api.py -v
```

### Expected Output:
```
======================== 26 passed, 1 warning in 5.89s ========================
```

### Run Frontend Static Checks:
```bash
cd frontend
npx oxlint
npm run build
```
*(Both pass with 0 errors and production build completes in <1s).*
