# ReServeAI — Platform Limitations & Architectural Boundaries

## 1. Overview
In accordance with the ReServeAI absolute engineering honesty policy, this document defines known operational limitations, environmental blockers, and boundaries of the current release.

---

## 2. Explicit System Limitations

### A. Computer Vision Freshness (Simulated Mode)
- **Status:** **SIMULATED** (`spectral-spatial-v2.1-SIMULATED`)
- **Limitation:** The genuine 2.79 GB multi-class fruit image dataset from Mendeley Data could not be staged through the host enterprise network environment (FortiGate SSL interception). Furthermore, the host `C:` drive has ~6.48 GB of free space, precluding local installation of Torch/CUDA without risking disk exhaustion.
- **Safety Policy:** The platform does NOT claim automated food safety certification. Freshness outputs are strictly advisory. Human inspector sign-off (`human_verified = True`) is mandatory before any food lot can be cleared for redistribution. Scope is limited to **fruit produce only**.

### B. Waste Prediction (Rule-Based Fallback)
- **Status:** **FALLBACK** (`rule-based-v1.0`)
- **Limitation:** The platform database currently contains 0 real historical kitchen waste production events. Training a high-capacity machine learning model (e.g. XGBoost) without genuine ground-truth production data would constitute synthetic fabrication.
- **Remediation:** A deterministic heuristic fallback calculates waste risk based on cold-chain breaches and shelf-life urgency until 1,000+ real commercial kitchen waste events are logged in production.

### C. E-Nose Meat Quality Scope
- **Status:** **TRAINED & LEAKAGE-AUDITED** (`enose-lgbm-v1.0-leakage-audited`)
- **Scope Boundary:** Evaluated strictly on the Mendeley E-Nose Beef Dataset. The model is valid **BEEF QUALITY ONLY**. It must NEVER be used to evaluate poultry, seafood, pork, vegetables, or dairy products.

### D. Remote Git Push (Host Network Policy)
- **Status:** **BLOCKED BY HOST FIREWALL**
- **Limitation:** The host enterprise network uses FortiGate deep packet inspection (`FG6H0FTB22905105`). Git HTTPS connections fail with `schannel: SEC_E_UNTRUSTED_ROOT (0x80090325)` due to corporate TLS MITM interception.
- **Remediation:** Commits are cleanly maintained on local branch `main`. Upstream push requires network administrator whitelist or corporate CA certificate installation into Git's trust store.
