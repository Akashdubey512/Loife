# ReServeAI — Production Deployment Guide

## 1. Prerequisites
- **Operating System:** Linux (Ubuntu 22.04 LTS / Debian 12 recommended for production container hosts) or Windows Server / 11 for local development.
- **Python:** Python 3.9+ (Python 3.11 recommended for production containers).
- **Node.js:** Node.js v20.x or v22.x LTS, with `npm` v10+.
- **Database:** PostgreSQL 15+ (Production) or SQLite 3.35+ (Local development & isolated testing).
- **In-Memory Cache / Broker:** Redis 7.x (Optional in standalone dev; required for distributed caching & pub/sub).
- **Container Engine:** Docker 24+ and Docker Compose v2.20+ (Optional for containerized deployments).
- **Reverse Proxy:** Nginx 1.24+ or Traefik with TLS termination.

---

## 2. Environment Variables & Configuration
Copy `.env.example` to `.env` in the project root:
```bash
cp .env.example .env
```
Key configuration parameters:
- `ENVIRONMENT`: Set to `production` (enforces strict security validation).
- `SECRET_KEY`: Generate a secure 64-character secret key:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  *(In production, `SECRET_KEY` MUST be at least 32 characters and cannot match known defaults).*
- `DATABASE_URL`: Connection string for PostgreSQL:
  `postgresql://reserve_user:SECURE_DB_PASSWORD@localhost:5432/reserve_ai_db`
- `BACKEND_CORS_ORIGINS`: Explicit list of trusted client origins, e.g.:
  `https://app.reserveai.org,https://admin.reserveai.org`
  *(Wildcard `*` is strictly forbidden in production with credentials enabled).*
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT lifetime (recommended: 1440 for standard operations or 60 for high-security environments).
- `AUTH_RATE_LIMIT_ENABLED`: `true`
- `AUTH_RATE_LIMIT_MAX_REQUESTS`: `10` per minute per IP for authentication endpoints.

---

## 3. Database Setup (PostgreSQL)
1. Initialize the PostgreSQL cluster and create user/database:
   ```sql
   CREATE USER reserve_user WITH PASSWORD 'SECURE_DB_PASSWORD';
   CREATE DATABASE reserve_ai_db OWNER reserve_user;
   GRANT ALL PRIVILEGES ON DATABASE reserve_ai_db TO reserve_user;
   ```
2. Verify connectivity:
   ```bash
   psql -U reserve_user -d reserve_ai_db -h localhost
   ```
3. Automatic schema initialization:
   On backend startup, SQLAlchemy runs `Base.metadata.create_all(bind=engine)` to ensure all 16 core tables, foreign keys, and indexes exist.
4. Production Seeding Policy:
   Automatic seeding is strictly **disabled** when `ENVIRONMENT=production`. To seed initial administrative accounts or baseline reference data manually:
   ```bash
   python seed_admin.py
   ```

---

## 4. Backend Startup

### Standard Host Process
```bash
# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or .\.venv\Scripts\Activate.ps1 on Windows

# Install production dependencies
pip install -r backend/requirements.txt

# Start production ASGI server with multi-worker Uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips='*'
```

### Docker Compose
```bash
docker compose up -d --build backend
```

---

## 5. Frontend Startup & Production Build

### Static Distribution Build
```bash
cd frontend
npm ci
npm run build
# Artifacts are generated in frontend/dist/
```

### Serving with Nginx
Serve the static bundle `frontend/dist/` via Nginx with reverse proxy to backend API:
```nginx
server {
    listen 80;
    server_name app.reserveai.org;
    root /var/www/reserveai/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 6. Model Artifact Requirements
Before starting backend inference services, ensure genuine model artifacts exist:
- `models/demand/demand_model.txt` & `metadata.json` (LightGBM Demand Regressor)
- `models/maintenance/maintenance_model.txt` & `metadata.json` (AI4I Predictive Maintenance Classifier)
- `models/energy/energy_model.txt` & `metadata.json` (Appliances Energy Regressor)
- `models/sensor/enose_model.txt` & `metadata.json` (Mendeley E-Nose Meat Quality Classifier — **Beef Only**)
- `ml/sustainability_engine.py` (Poore & Nemecek 42-product lookup matrix)
- `backend/routing/engine.py` & `logistics/optimizer.py` (Clarke-Wright Savings + 2-Opt)

**Non-Artifact / Fallback Components:**
- Fruit CV runs honestly in `spectral-spatial-v2.1-SIMULATED` simulation mode.
- Waste prediction runs honestly in `rule-based-v1.0` fallback.

Verify artifacts via validation script:
```bash
python ml/pipelines/validate_datasets.py
```

---

## 7. Health Checks & Probes
ReServeAI provides standardized endpoints for load balancers and orchestrators:
- **Liveness Probe:** `GET /health/live`
  - Returns `200 OK` (`{"status": "ALIVE", "process": "running"}`)
- **Readiness Probe:** `GET /health/ready`
  - Validates database connectivity, configuration, and model registry availability.
  - Returns `200 OK` with individual component statuses (`application`, `database`, `authentication`, `model_registry`, etc.).
  - Returns `503 Service Unavailable` if the database is unreachable.
- **Legacy Orchestrator Health:** `GET /health`
  - Returns `200 OK` (`{"status": "HEALTHY", "database": "connected"}`)

---

## 8. Production Configuration Safeguards
When `ENVIRONMENT=production`:
- Swagger UI (`/docs`), ReDoc (`/redoc`), and OpenAPI schema (`/openapi.json`) are automatically **disabled**.
- Weak or default `SECRET_KEY` values immediately abort application startup.
- CORS wildcard `*` is strictly forbidden.
- Detailed SQL exceptions and stack traces are suppressed from client responses.

---

## 9. Shutdown Procedure
To gracefully stop running services:
```bash
# Standalone systemd / terminal
kill -TERM <PID>

# Docker Compose
docker compose down
```
Uvicorn will finish in-flight requests, close active WebSocket connections cleanly, and dispose of database pool connections.

---

## 10. Troubleshooting
1. **Database Connection Refused:**
   - Verify PostgreSQL service is active: `systemctl status postgresql`
   - Check credentials in `.env` match PostgreSQL role.
2. **CORS Origin Rejected:**
   - Ensure the browser's exact domain and scheme (e.g., `https://app.reserveai.org`) are present in `BACKEND_CORS_ORIGINS`.
3. **ML Service / Status Reports 'artifact_missing':**
   - Verify file permissions and paths in `models/model_registry.json`. Run `python ml/pipelines/validate_datasets.py`.
4. **JWT Expiration / Invalid Token:**
   - Ensure client and server system clocks are synchronized via NTP.
