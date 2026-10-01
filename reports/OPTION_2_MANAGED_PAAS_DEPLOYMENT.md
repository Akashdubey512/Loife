# Option 2: Managed Cloud PaaS Deployment Guide (Render + Vercel + Supabase)

This guide provides step-by-step instructions to deploy **reServe AI (Loife)** using managed cloud PaaS services with **zero server administration**.

---

## 1. Stack Allocation (Free / Low Cost Tier)

| Service | Cloud Provider | Free Tier Availability | URL Format |
| :--- | :--- | :--- | :--- |
| **PostgreSQL Database** | Supabase (`supabase.com`) or Render | 500 MB Free | `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres` |
| **Redis Cache** | Upstash (`upstash.com`) or Render | 10k requests/day Free | `rediss://default:[PASSWORD]@[HOST].upstash.io:6379` |
| **Backend & ML Microservices** | Render (`render.com`) | Free Web Services | `https://reserve-ai-backend.onrender.com` |
| **React Frontend SPA** | Vercel (`vercel.com`) | Unlimited Free | `https://reserve-ai.vercel.app` |

---

## Step 1: Create Database & Redis Instances

### A. PostgreSQL Database (Supabase)
1. Go to [https://supabase.com](https://supabase.com) and sign in with GitHub.
2. Click **New Project** -> Name it `reServe-AI`.
3. Set a strong **Database Password** (e.g. `ReserveSecurePass2026!`).
4. Select region (e.g., `US East` or `Singapore`).
5. Once created, go to **Project Settings** -> **Database** -> Copy your **URI Connection String**:
   `postgresql://postgres.xxxx:ReserveSecurePass2026!@aws-0-us-east-1.pooler.supabase.com:6543/postgres`

### B. Redis Instance (Upstash)
1. Go to [https://upstash.com](https://upstash.com) and sign in with GitHub.
2. Click **Create Database** -> Name it `reserve-redis`.
3. Choose **Primary Region** -> Click **Create**.
4. Copy the **redis://** or **rediss://** connection URL under `UPSTASH_REDIS_REST_URL` / `Details`.

---

## Step 2: Deploy ML Microservice & Backend API on Render

Render will read your repository configuration directly via `render.yaml` or manual service setup.

### Option A: Automatic Blueprint Deployment (Recommended)
1. Log in to [https://render.com](https://render.com) with GitHub.
2. Click **New +** -> **Blueprint**.
3. Connect your repository: `https://github.com/Akashdubey512/ReServeAi`.
4. Render will automatically detect `render.yaml` and create both services:
   - `reserve-ai-ml-service`
   - `reserve-ai-backend`
5. Under `envVars`, enter your connection strings:
   - `DATABASE_URL` = (Your Supabase PostgreSQL URL)
   - `REDIS_URL` = (Your Upstash Redis URL)
6. Click **Apply**. Render will build and deploy both services!

### Option B: Manual Web Service Creation (Alternative)

#### 1. ML Microservice
- **Name**: `reserve-ai-ml-service`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r ml/requirements.txt`
- **Start Command**: `python -m ml.service`
- **Environment Variables**:
  - `ML_PORT` = `8001`

#### 2. Backend API Service
- **Name**: `reserve-ai-backend`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `ENVIRONMENT` = `production`
  - `SECRET_KEY` = `e8f93a1c5b4d7e2f6a0b1c3d5e7f9a2b4c6d8e0f1a3b5c7d9e1f3a5b7c9d1e3f`
  - `DATABASE_URL` = (Your Supabase connection string)
  - `REDIS_URL` = (Your Upstash connection string)
  - `ML_SERVICE_URL` = `http://reserve-ai-ml-service:8001` (or its public Render URL)

Once deployed, copy your Backend live URL (e.g. `https://reserve-ai-backend.onrender.com`).

---

## Step 3: Deploy Frontend on Vercel

1. Log in to [https://vercel.com](https://vercel.com) with GitHub.
2. Click **Add New...** -> **Project**.
3. Import `Akashdubey512/ReServeAi`.
4. Configure Project Settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Expand **Environment Variables**:
   - `VITE_API_BASE_URL` = `https://reserve-ai-backend.onrender.com/api/v1`
6. Click **Deploy**.

Vercel will build the frontend and provide your live URL (e.g., `https://reserve-ai.vercel.app`).

---

## Step 4: Verification

1. **Test Backend**: Open `https://reserve-ai-backend.onrender.com/health` in your browser. Expected response:
   ```json
   {"status":"HEALTHY","database":"connected","environment":"production"}
   ```
2. **Test Frontend App**: Open `https://reserve-ai.vercel.app`.
   - Register/login as kitchen manager or admin.
   - Run live demand forecasts, quality image scans, and route optimizations!
