# ReServeAI — Project Evaluation & Viva Cheat Sheet

This document provides concise, factually grounded answers to common technical and architectural questions during project evaluations and technical reviews.

---

### 1. What problem does ReServeAI solve?
Commercial and institutional dining facilities waste up to 30-40% of prepared food due to unpredictable demand, lack of real-time cold-chain visibility, and uncoordinated logistics for surplus donation. ReServeAI integrates predictive forecasting, sensory quality control, automated NGO matching, route optimization, and sustainability accounting into a single closed-loop ecosystem.

### 2. Why focus on food redistribution?
Food waste generates 8-10% of global greenhouse gases while millions face food insecurity. Landfilling edible food squanders all the water, arable land, and energy embedded in its production. Redistribution captures this embedded value and routes nutrition to people in need before spoilage occurs.

### 3. Why use AI/ML instead of traditional heuristic software?
Traditional software relies on static thresholds that cannot capture complex non-linear patterns—such as the impact of multi-day weather shifts and promotional price elasticity on institutional meal consumption, or multi-channel microclimate dynamics on appliance energy draw. Machine learning models generalize from historical time-series data to deliver accurate, localized predictions.

### 4. What datasets were used across the platform?
- **Genpact Food Demand Forecasting:** 50,000 real fulfillment center order records across 51 meal types.
- **AI4I 2020 Predictive Maintenance (UCI):** 10,000 machine failure records with physical process telemetry.
- **Appliances Energy Prediction (UCI):** 19,735 environmental microclimate measurements from a low-energy house.
- **Mendeley E-Nose Beef Quality:** 20,815 gas sensor time-series measurements across 4 spoilage classes.
- **CVRPLIB (PUC-Rio):** 9 standard Augerat Set A Capacitated Vehicle Routing problem instances.
- **Poore & Nemecek (2018) Science:** Meta-analysis covering 38,700 farms and 42 agricultural commodities.

### 5. Which models are genuinely trained?
Four models are genuinely trained and backed by serialized LightGBM artifacts:
1. **Demand Forecasting (`demand-lgbm-v1.0`):** LightGBM Regressor (`models/demand/`).
2. **Predictive Maintenance (`maint-lgbm-v1.0`):** LightGBM Multi-Class Classifier (`models/maintenance/`).
3. **Appliances Energy (`energy-lgbm-v1.0`):** LightGBM Regressor (`models/energy/`).
4. **E-Nose Meat Quality (`enose-lgbm-v1.0-leakage-audited`):** LightGBM 4-Class Classifier (`models/sensor/`).

### 6. Which models are simulated or fallback?
1. **Fruit CV Classifier (`spectral-spatial-v2.1-SIMULATED`):** Runs in simulation mode.
2. **Waste Classification (`rule-based-v1.0`):** Runs in deterministic rule-based fallback mode.

### 7. Why is the Fruit CV model in simulation mode?
The legitimate 2.79 GB Mendeley multi-class fruit image archive could not be downloaded through the host enterprise network filter (FortiGate SSL MITM interception). Furthermore, the host `C:` drive had ~6.48 GB of free space, precluding local installation of PyTorch/CUDA without risking disk exhaustion. In adherence to our absolute honesty policy, we did not fabricate CNN weights. The system runs an advisory colorimetric simulation and mandates physical human verification.

### 8. Why is the Waste ML model in fallback mode?
The platform database currently contains 0 real historical kitchen waste production events. Training a gradient-boosted ML model on fabricated or synthetic data would constitute dishonest engineering. The system honestly uses a cold-chain threshold heuristic until 1,000+ real operational waste logs accumulate.

### 9. How was data leakage audited and handled in the E-Nose model?
During our Phase 10B/11 audits, we identified that the dataset's Total Viable Count (TVC) column was a direct proxy for the ground-truth target label. Including TVC artificially inflated test accuracy. We excised TVC completely from the feature inputs, retraining the LightGBM classifier solely on ambient temperature, humidity, and the 8 MOS gas sensors (`mq2`-`mq138`), achieving a genuine, leakage-audited accuracy of **93.10%** and Macro-F1 of **0.8718**.

### 10. Why is the E-Nose model restricted strictly to beef quality?
The underlying dataset (doi:10.17632/n8mc3nspfn.1) was collected exclusively from beef samples stored across controlled degradation intervals. Gas emissions, microbial flora, and volatile organic compound (VOC) profiles differ fundamentally between beef, poultry, fish, and produce. Claiming universal food quality would be scientifically invalid; therefore, the model and API explicitly enforce `scope: "BEEF_QUALITY_ONLY"`.

### 11. How does route optimization work in ReServeAI?
It solves the Capacitated Vehicle Routing Problem (CVRP) by assigning multiple delivery stops to available vehicles such that vehicle capacity constraints are strictly respected while minimizing total transit distance and shelf-life urgency penalties.

### 12. Why was Clarke-Wright Savings with 2-Opt chosen over basic nearest-neighbor?
Greedy nearest-neighbor heuristics often produce route crossings, suboptimal clusters, and capacity over-allocations. Clarke-Wright calculates the savings $s_{ij} = d(0, i) + d(0, j) - d(i, j)$ of combining two stops onto one vehicle. Intra-route 2-Opt local search then iteratively untangles crossings, achieving 100% capacity feasibility and reducing the distance gap vs Best Known Solutions down to **4.07%** in sub-millisecond runtimes (~0.06 ms).

### 13. How does the ESG sustainability calculation work?
When a surplus food batch is marked `DELIVERED`, the system multiplies the food item's mass by its specific life-cycle assessment (LCA) coefficients derived from Poore & Nemecek (2018) Science Table S2. This computes CO2e avoided (kg), freshwater conserved (Liters), and diverted meal equivalents.

### 14. How does the authentication system work?
User passwords are encrypted with PBKDF2 using HMAC-SHA256, 100,000 rounds, and unique cryptographic salts. Upon successful authentication, the server issues a cryptographically signed HS256 JWT access token containing the user ID and expiration timestamp.

### 15. How does Role-Based Access Control (RBAC) work?
FastAPI route handlers use dependency injection (`require_roles(["ROLE_NAME"])`) to inspect the decoded JWT claims before executing endpoint logic. If the user lacks the required permission, the server returns HTTP 403 Forbidden.

### 16. How is multi-tenant organizational isolation enforced?
The backend validates `check_tenant_access(user, organization_id)` on every query and mutation. Users cannot read or modify kitchen inventory, surplus batches, or routes belonging to an unrelated organization, preventing IDOR (Insecure Direct Object Reference) vulnerabilities.

### 17. How are file uploads secured?
File uploads (e.g. food quality scan images) are capped at 5 MB. The backend inspects the binary magic bytes (`\xff\xd8\xff` for JPEG, `\x89PNG` for PNG, `RIFF...WEBP` for WebP), rejecting executables, scripts, or corrupted files with HTTP 400 or 413.

### 18. How is backup and recovery handled?
For PostgreSQL in production, standard `pg_dump` binary archives are taken. For SQLite in development, the non-blocking online backup API (`sqlite3.backup`) creates atomic snapshots without blocking concurrent write transactions. Restoration was empirically verified with 23 tables and 71 user records preserved without corruption.

### 19. What health probes are exposed and why are they separated?
- `GET /health/live`: Liveness probe indicating whether the process is alive (returns HTTP 200 `ALIVE`).
- `GET /health/ready`: Readiness probe verifying database connectivity and configuration. Optional degraded states (such as simulated CV or fallback waste) do not falsely fail overall readiness.

### 20. What are the major known limitations of the current release?
1. Fruit CV operates in simulation mode with mandatory physical human verification.
2. Waste ML operates in rule-based fallback mode due to 0 real historical waste records.
3. E-Nose is strictly constrained to beef products.
4. Git push to GitHub is blocked by the host enterprise FortiGate SSL deep-packet inspection policy.

### 21. What would be the next steps once additional real-world data is available?
1. Collect 1,000+ real commercial kitchen disposal events to train a production XGBoost waste model.
2. Stage the 2.79 GB Mendeley fruit dataset on an external GPU cloud host to train genuine ResNet/EfficientNet weights for fruit classification.
3. Import the corporate CA certificate into the Git trust store to publish upstream to GitHub.
