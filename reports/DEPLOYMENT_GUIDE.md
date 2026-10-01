# reServe AI (Loife) - Production Deployment Guide

This guide provides step-by-step instructions on **where** and **how** to deploy the complete **reServe AI** platform for production or hackathon evaluation.

---

## Architecture Overview

The system consists of 5 core services:
1. **Frontend**: React 18 + Vite SPA (served via Nginx on port `3000`/`80`)
2. **Backend API**: FastAPI + Uvicorn (port `8000`)
3. **ML Microservice**: FastAPI ML Inference Engine (port `8001`)
4. **Database**: PostgreSQL 15 (port `5432`)
5. **Cache / Message Queue**: Redis 7 (port `6379`)

---

## Option 1: Docker Compose on Single Cloud VPS (Recommended & Easiest)

> **Ideal for**: AWS EC2, DigitalOcean Droplet, Hetzner, Linode, Render VPS  
> **Estimated Cost**: ~$5 – $12/month (or Free Tier on AWS / Oracle Cloud)

### Step 1: Provision Cloud Virtual Private Server (VPS)
1. Create a VPS with **Ubuntu 22.04 LTS** (minimum 2 vCPU, 4GB RAM recommended).
2. SSH into your server:
   ```bash
   ssh root@YOUR_SERVER_IP
   ```

### Step 2: Install Docker & Docker Compose
Run the following commands on your server:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl enable --now docker
```

### Step 3: Clone Codebase & Configure Environment
1. Clone the repository:
   ```bash
   git clone https://github.com/Akashdubey512/ReServeAi.git
   cd ReServeAi
   ```
2. Create production `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` to set secure secrets:
   ```env
   ENVIRONMENT=production
   SECRET_KEY=generate-a-random-64-char-hex-key
   POSTGRES_USER=reserve_user
   POSTGRES_PASSWORD=your_secure_db_password
   POSTGRES_DB=reserve_ai_db
   DATABASE_URL=postgresql://reserve_user:your_secure_db_password@postgres:5432/reserve_ai_db
   REDIS_URL=redis://redis:6379/0
   ML_SERVICE_URL=http://ml-service:8001
   BACKEND_CORS_ORIGINS="http://YOUR_SERVER_IP,http://yourdomain.com"
   ```

### Step 4: Launch Container Suite
Run Docker Compose to build and start all 5 containers:
```bash
docker compose up -d --build
```

### Step 5: Verify Live Deployment
1. Check running containers:
   ```bash
   docker compose ps
   ```
2. Test backend health check:
   ```bash
   curl http://localhost:8000/health
   ```
3. Open your browser and navigate to:
   - **Frontend App**: `http://YOUR_SERVER_IP:3000`
   - **API Documentation**: `http://YOUR_SERVER_IP:8000/api/v1/docs`

---

## Option 2: Fully Managed PaaS (Render / Railway + Vercel)

> **Ideal for**: Zero server management, auto-scaling, SSL certificates included  
> **Estimated Cost**: Free Tier available / ~$7/month

### 1. Database & Cache (Managed)
- **Database**: Create a free PostgreSQL instance on **Supabase** (`https://supabase.com`) or **Render** (`https://render.com`).
- **Redis**: Create a free Redis instance on **Upstash** (`https://upstash.com`) or **Render**.
- Save your connection string `DATABASE_URL` and `REDIS_URL`.

### 2. Backend & ML Microservice Deployment (Render / Railway)
1. **Connect GitHub**: Sign in to Render/Railway and connect `https://github.com/Akashdubey512/ReServeAi`.
2. **Deploy ML Microservice**:
   - Build Command: `pip install -r ml/requirements.txt`
   - Start Command: `python -m ml.service`
   - Environment Variable: `ML_PORT=8001`
3. **Deploy Backend API**:
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
   - Environment Variables:
     - `DATABASE_URL` = (Your Supabase/Render PostgreSQL URL)
     - `REDIS_URL` = (Your Upstash/Render Redis URL)
     - `ML_SERVICE_URL` = (Your deployed ML Microservice URL)
     - `SECRET_KEY` = (Generated 64-char hex key)
     - `ENVIRONMENT` = `production`

### 3. Frontend Deployment (Vercel / Netlify)
1. Import repository in **Vercel** (`https://vercel.com`).
2. Root Directory: `frontend`
3. Framework Preset: `Vite`
4. Build Command: `npm run build`
5. Output Directory: `dist`
6. Environment Variables:
   - `VITE_API_BASE_URL` = `https://your-backend-api.onrender.com/api/v1`

---

## Summary of Access Endpoints

| Service | Local / Docker URL | Cloud Production URL Example |
| :--- | :--- | :--- |
| **Frontend Application** | `http://localhost:3000` | `https://reserveai.vercel.app` or `http://YOUR_SERVER_IP:3000` |
| **Backend API Docs (Swagger)** | `http://localhost:8000/api/v1/docs` | `https://api.reserveai.com/api/v1/docs` |
| **Backend Health Check** | `http://localhost:8000/health` | `https://api.reserveai.com/health` |
| **ML Service Port** | `http://localhost:8001` | Private internal container network |
