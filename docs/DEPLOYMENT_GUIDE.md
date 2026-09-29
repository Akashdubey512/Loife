# reServe AI — Production Deployment & Local Setup Guide

This guide covers deployment instructions for **Windows**, **Linux/macOS**, and **Docker Compose**.

---

## 1. Prerequisites

- **Python**: Version 3.10+ (Tested on Python 3.11 and 3.13)
- **Node.js**: Version 18+ (Tested on Node 20 LTS)
- **Database**: PostgreSQL 15+ (Production) or SQLite (Local Development)
- **Docker**: Docker Engine 24+ and Docker Compose v2+ (Optional for containerized run)

---

## 2. Environment Variables

Create `.env` in the project root (copied from `.env.example`):

```bash
# Server & Environment
ENVIRONMENT=production
PORT=8000
SECRET_KEY=reserve-ai-super-secure-production-jwt-secret-key-2026
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Database Configuration
DATABASE_URL=postgresql://reserve_user:reserve_secure_pass@localhost:5432/reserve_ai_db
# For lightweight local SQLite, use:
# DATABASE_URL=sqlite:///./reserve_ai.db

# Cache & Messaging
REDIS_URL=redis://localhost:6379/0

# Internal ML Service URL
ML_SERVICE_URL=http://localhost:8001

# CORS Allowed Origins
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://127.0.0.1:3000"]
```

---

## 3. Local Deployment (Windows)

### Option A: Using the Automated PowerShell Script
```powershell
.\run_local.ps1
```

### Option B: Manual Step-by-Step

1. **Backend Initialization**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   ```

2. **Database Seeding**:
   ```powershell
   python -c "from backend.core.database import Base, engine; from backend.services.seed_service import seed_database; Base.metadata.create_all(bind=engine); seed_database()"
   ```

3. **Start FastAPI Backend (Port 8000)**:
   ```powershell
   uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Frontend Initialization & Start (In a separate terminal)**:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
   Access the frontend console at `http://localhost:5173`.

---

## 4. Local Deployment (Linux / macOS)

1. **Clone & Virtual Environment**:
   ```bash
   git clone https://github.com/reserveai/reserve-ai.git
   cd reserve-ai
   python3 -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   ```

2. **Initialize Database**:
   ```bash
   python3 -c "from backend.core.database import Base, engine; from backend.services.seed_service import seed_database; Base.metadata.create_all(bind=engine); seed_database()"
   ```

3. **Start Backend**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

4. **Build and Serve Frontend**:
   ```bash
   cd frontend
   npm install
   npm run build
   # Serve with any static web server or dev server:
   npm run dev
   ```

---

## 5. Containerized Deployment (Docker Compose)

The multi-container stack launches 5 isolated services:
1. `postgres`: PostgreSQL 15 database with persistent volume.
2. `redis`: Redis 7 in-memory cache and message broker.
3. `ml-service`: Standalone Python ML microservice (Port 8001).
4. `backend`: FastAPI application service with database connection pooling and healthcheck (Port 8000).
5. `frontend`: Multi-stage production Nginx container serving React 19 app and reverse proxying `/api/` (Port 3000).

### Execution Command:
```bash
docker compose up -d --build
```

### Healthcheck Verification:
```bash
docker compose ps
curl -f http://localhost:8000/health
```

### Service URL Map:
| Service | URL | Default Credentials |
|---|---|---|
| **Web Console** | `http://localhost:3000` | N/A |
| **API Swagger UI** | `http://localhost:8000/docs` | `admin@reserveai.com` / `Admin@1234` |
| **ML Engine Health** | `http://localhost:8001/health` | Internal service network |
| **PostgreSQL** | `localhost:5432` | `reserve_user` / `reserve_secure_pass` |
| **Redis** | `localhost:6379` | Default no-auth internal |

---

## 6. Seed Credentials for Demonstration

| Role | Email | Password | Primary Dashboard |
|---|---|---|---|
| **Super Admin / Sustainability Director** | `admin@reserveai.com` | `Admin@1234` | Executive & Sustainability Dashboards |
| **Kitchen Executive Chef** | `kitchen@reserveai.com` | `Kitchen@1234` | Kitchen & Demand Dashboards |
| **Chief Quality & Safety Inspector** | `quality@reserveai.com` | `Quality@1234` | Quality Assessment Dashboard |
| **Fleet Logistics Dispatcher** | `logistics@reserveai.com` | `Logistics@1234` | Logistics & Routing Dashboard |
