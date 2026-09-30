# Phase 13 Baseline Audit Report

**Date:** 2026-10-01  
**Project:** ReServeAI  
**Auditor:** Automated Engineering Hardening Agent  

---

## 1. Verified Baseline State

- **Current Git Commit:** `baddff6` (`chore(cv): document fruit training infrastructure blocker`)
- **Current Branch:** `main`
- **Working Tree:** Clean (all changes tracked and committed)
- **Pytest Suite:** **169 / 169 tests passing** (0 failures, 8 library warnings in 6.67s)
- **Dataset Validation Pipeline:** **59 / 59 checks passing** (`ml/pipelines/validate_datasets.py`)
- **Frontend Production Build:** **Passed** (`tsc -b && vite build` completed in 1.15s with 0 errors)
- **Host Hardware:** NVIDIA GeForce RTX 3050 Laptop GPU (6,144 MiB VRAM), Driver 581.86, CUDA 13.0
- **Storage Profile:**
  - Drive `C:` (System OS): **6.46 GB Free** (Critically constrained)
  - Drive `D:` (Project Workspace): **110.58 GB Free** (Optimal headroom)

---

## 2. ML Engine Registry State

| Engine | Version | Registry Status | Scope / Method |
| :--- | :--- | :--- | :--- |
| **Demand Forecasting** | `demand-lgbm-v1.0` | `trained` | LightGBM Fulfilment Centers |
| **Predictive Maintenance** | `maint-lgbm-v1.0` | `trained` | Kitchen Machinery Anomaly Detection |
| **Appliances Energy** | `energy-lgbm-v1.0` | `trained` | Kitchen Appliance Energy Profile |
| **E-Nose Meat Quality** | `enose-lgbm-v1.0-leakage-audited` | `trained` | **BEEF QUALITY ONLY** (93.10% Acc / 0.8718 F1) |
| **Fruit Freshness** | `spectral-spatial-v2.1-SIMULATED` | `simulated` | Colorimetric Spectral-Spatial (Fruits only) |
| **Waste Prediction** | `rule-based-v1.0` | `fallback` | Heuristic Baseline (0 DB records) |
| **Sustainability / LCA** | `poore-nemecek-v2.0` | `lookup` | 42 Products Lookup Table |
| **Vehicle Routing (VRP)** | `clarke-wright-2opt-v2.0` | `active` | Combinatorial Optimization (+4.07% vs BKS) |

---

## 3. Known Documented Blockers

1. **Host Network Git Push Policy:** Host network FortiGate firewall intercepts SSL certificates and terminates outbound smart HTTP push (`git-receive-pack`) with return code 52.
2. **Fruit CV S3 Ingress Throttling:** Mendeley S3 download throughput is 0.27–0.97 MB/s, and long-lived TCP streams are terminated by the firewall. Model remains honestly marked as simulated pending local archive extraction.
3. **Waste ML Production Data Requirement:** SQLite database currently contains 0 historical waste event records. Engine legitimately operates on `rule-based-v1.0` fallback.
