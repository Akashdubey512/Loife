# ReServeAI — Operational Monitoring Plan

## 1. Overview
The ReServeAI platform utilizes a lightweight, proactive observability framework designed to detect operational bottlenecks, service failures, authentication anomalies, and machine learning drifts without imposing heavy infrastructural overhead.

---

## 2. Core Monitoring Domains

| Domain | Metrics / Signals | Collection Mechanism | Healthy Baseline | Degraded Threshold | Alerting Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Liveness & Process** | Process uptime, PID status | `GET /health/live` | HTTP 200 `ALIVE` | Process crash / non-responsive | Process supervisor (systemd / Docker) restarts process automatically. |
| **System Readiness** | DB connection pool, Model registry availability | `GET /health/ready` | HTTP 200 `READY` | HTTP 503 `NOT_READY` (DB down) | High-priority P1 alert to DevOps; investigate database server. |
| **Authentication & Access** | Failed login attempts, invalid JWTs, 401/403 status codes | Structured API error logs & Rate limiter events | < 5 failures / min | > 20 failures / min | Rate limiter engages (10 req/min/IP). Suspected brute-force triggers security log alert. |
| **API Latency & Errors** | Response times, HTTP 500 rate | Uvicorn / Reverse Proxy access logs | 95th percentile < 150 ms; 5xx errors < 0.1% | 5xx errors > 1% or latency > 500 ms | Inspect application logs for unhandled exceptions or resource starvation. |
| **Database Pool & Transactions** | Active connections, pool wait time, failed rollbacks | SQLAlchemy engine metrics & DB logs | Active connections < 80% pool; rollback rate ~ 0% | Connection pool exhausted; deadlock detected | Increase pool size; kill stale transaction locks. |
| **ML Demand Forecasting** | Latency, LightGBM inference exceptions | Endpoint `/api/v1/demand/predict` | Latency < 60 ms; 100% predictions returned | Fallback heuristic triggered or model missing | Verify `models/demand/demand_model.txt` integrity. |
| **Predictive Maintenance** | Latency, feature vector validation | Endpoint `/api/v1/maintenance/evaluate` | Latency < 30 ms; categorical features valid | Input schema errors | Review appliance sensor payload formatting. |
| **E-Nose Meat Quality** | Input channel bounds (MQ sensors), inference time | Endpoint `/api/v1/sensors/enose/evaluate` | Latency < 10 ms; features within sensor range | Features out-of-range or beef scope exceeded | Log telemetry warning; ensure operator inspects sensor calibration. |
| **Fruit CV Quality** | Scan volume, simulation indicator check | Endpoint `/api/v1/quality/scan` | Latency < 50 ms; returns simulated state + human prompt | Missing human verification flag | Enforce UI banner requiring manual operator confirmation. |
| **Waste Classification** | Event count, fallback indicator | Endpoint `/api/v1/waste/predictions` | Rule-based response within 5 ms | Unexpected server error | Ensure database event logging remains intact. |
| **Route Optimization (VRP)**| Solution feasibility, execution time | Endpoint `/api/v1/logistics/optimize-route` | 100% feasible solutions; time < 50 ms | Greedy fallback invoked | Verify delivery coordinates and vehicle capacity constraints. |
| **File Upload Storage** | Upload reject count (413/400), disk usage | Upload router metrics | Rejected files < 1%; disk usage < 80% | Storage > 85% full | Trigger storage cleanup of temporary scan artifacts. |

---

## 3. Degraded vs. Failed State Strategy
ReServeAI distinguishes graceful operational degradation from systemic failure:
- **Graceful Degradation:**
  - If Fruit CV operates in simulation mode (`spectral-spatial-v2.1-SIMULATED`), the system continues normal operations with human verification prompts.
  - If Waste ML operates in rule-based fallback, waste calculations proceed deterministically without downtime.
  - If external OSRM routing is unreachable, the internal Euclidean + 2-Opt heuristic optimizer takes over seamlessly.
- **Critical Failure:**
  - Database connectivity loss marks `/health/ready` as `NOT_READY` (HTTP 503) and pauses transaction-dependent operations until recovered.

---

## 4. Operational Runbook & Response Procedures
1. **Unhealthy Readiness Check:**
   - Execute: `curl -i http://localhost:8000/health/ready`
   - If `database: "unavailable"`, check database process status (`systemctl status postgresql` or verify local SQLite file lock).
2. **Elevated Rate Limit Rejections:**
   - Review `/var/log/reserveai/access.log` for offending IP addresses.
   - If legitimate traffic is throttled, adjust `AUTH_RATE_LIMIT_MAX_REQUESTS` in `.env`.
3. **Model Registry Mismatch:**
   - Run `python ml/pipelines/validate_datasets.py` to pinpoint corrupted or moved model weights.
