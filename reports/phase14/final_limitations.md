# Phase 14 — Final Limitations Register

**Release Evaluation Date:** 2026-10-01  
**Platform:** ReServeAI (v1.0.0-rc1)

---

## 1. Limitations Register Table

| ID | Area | Issue Description | Classification | Impact on Production Release | Mitigation / Operational Runbook |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LIM-01** | **Computer Vision** | Fruit CV model runs in simulation mode (`spectral-spatial-v2.1-SIMULATED`) because the legitimate 2.79 GB Mendeley training dataset could not be downloaded through the host network filter. Host `C:` drive has ~6.48 GB free. | **EXTERNAL / MEDIUM** | Does not block release. Platform operates with mandatory human verification flag. | API explicitly sets `simulated=True` and `food_safety_verdict=PENDING_HUMAN_VERIFICATION`. Quality inspectors must physically verify produce before clearance. |
| **LIM-02** | **Waste Intelligence**| Waste prediction operates in rule-based fallback mode (`rule-based-v1.0`) because the database currently contains 0 real historical kitchen waste records. | **LOW** | Does not block release. Rule-based engine handles waste forecasting deterministically. | Retain rule-based heuristic until 1,000+ real kitchen production and disposal logs are captured in production. |
| **LIM-03** | **Sensor Intelligence**| E-Nose classifier is trained on Mendeley dataset with TVC target leakage audited out. Scope is strictly constrained to beef products. | **LOW (By Design)**| Does not block release. Fully functional within defined scope. | Enforce strict schema validation. The API returns `scope: "BEEF_QUALITY_ONLY"` and warns against evaluating other food categories. |
| **LIM-04** | **Deployment / Git** | Host enterprise firewall (`FG6H0FTB22905105`) intercepts HTTPS TLS connections with untrusted root certificate, blocking `git push origin main`. | **EXTERNAL** | Does not block release or local execution. Prevents remote GitHub sync from this host. | All code and reports are committed cleanly to local git branch `main`. Upstream sync to be performed once corporate CA is imported into Git schannel. |
| **LIM-05** | **Storage Engine** | Local environment uses SQLite 3.35+ single-file database (`reserve_ai.db`). Point-In-Time Recovery (PITR) is unavailable without PostgreSQL WAL archiving. | **LOW (Dev Environment)** | Production deployment configuration specifies PostgreSQL 15+ via Docker Compose. | Run `pg_dump` on PostgreSQL in production containers; utilize online SQLite backup API in development. |

---

## 2. Integrity Certification
None of the above limitations represent critical code bugs, unhandled exceptions, or architectural defects. All limitations represent documented external infrastructure realities or deliberate fail-safe defaults designed to protect human food safety and data integrity.
