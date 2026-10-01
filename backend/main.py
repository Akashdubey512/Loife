import os
import sys
import json
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure project root is in sys.path when invoked from within backend/ or root
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.database import Base, engine, get_db
from backend.services.seed_service import seed_database

# Import routers
from backend.auth.router import router as auth_router
from backend.users.router import router as users_router
from backend.organizations.router import router as orgs_router
from backend.kitchens.router import router as kitchens_router
from backend.inventory.router import router as inventory_router
from backend.production.router import router as production_router
from backend.demand.router import router as demand_router
from backend.waste.router import router as waste_router
from backend.quality.router import router as quality_router
from backend.sensors.router import router as sensors_router
from backend.energy.router import router as energy_router
from backend.maintenance.router import router as maintenance_router
from backend.redistribution.router import router as redistribution_router
from backend.logistics.router import router as logistics_router
from backend.sustainability.router import router as sustainability_router
from backend.notifications.router import router as notifications_router
from backend.analytics.router import router as analytics_router
from backend.ml_status import router as ml_status_router

import logging

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("reserve_ai.platform")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing reServe AI platform (Environment: %s)", settings.ENVIRONMENT)
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)
    try:
        from backend.models.entities import User
        from backend.core.database import SessionLocal
        db = SessionLocal()
        user_count = db.query(User).count()
        db.close()
        if user_count == 0:
            logger.info("Empty database detected. Seeding initial demo accounts...")
            seed_database(force=True)
            logger.info("Initial database seeding completed successfully.")
    except Exception as e:
        logger.warning("Auto-seed check caught: %s", str(e))
    logger.info("reServe AI platform services operational.")
    yield
    logger.info("Shutting down reServe AI platform services cleanly.")

is_production = (settings.ENVIRONMENT or "development").lower() == "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Enterprise AI-Powered Food Waste Reduction & Sustainable Redistribution Platform (SIH 2026)",
    openapi_url=None if is_production else f"{settings.API_V1_STR}/openapi.json",
    docs_url=None if is_production else f"{settings.API_V1_STR}/docs",
    redoc_url=None if is_production else f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "Origin"],
)

# Mount all 17 routers under /api/v1
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(orgs_router, prefix=f"{settings.API_V1_STR}/organizations", tags=["Organizations"])
app.include_router(kitchens_router, prefix=f"{settings.API_V1_STR}/kitchens", tags=["Kitchens"])
app.include_router(inventory_router, prefix=f"{settings.API_V1_STR}/inventory", tags=["Inventory"])
app.include_router(production_router, prefix=f"{settings.API_V1_STR}/production", tags=["Production"])
app.include_router(demand_router, prefix=f"{settings.API_V1_STR}/demand", tags=["Demand Forecasting"])
app.include_router(waste_router, prefix=f"{settings.API_V1_STR}/waste", tags=["Waste Prediction & Events"])
app.include_router(quality_router, prefix=f"{settings.API_V1_STR}/quality", tags=["Computer Vision Quality"])
app.include_router(sensors_router, prefix=f"{settings.API_V1_STR}/sensors", tags=["IoT Sensors"])
app.include_router(energy_router, prefix=f"{settings.API_V1_STR}/energy", tags=["Energy Efficiency"])
app.include_router(maintenance_router, prefix=f"{settings.API_V1_STR}/maintenance", tags=["Predictive Maintenance"])
app.include_router(redistribution_router, prefix=f"{settings.API_V1_STR}/redistribution", tags=["Surplus Redistribution"])
app.include_router(logistics_router, prefix=f"{settings.API_V1_STR}/logistics", tags=["Logistics & Routing"])
app.include_router(sustainability_router, prefix=f"{settings.API_V1_STR}/sustainability", tags=["Sustainability & ESG"])
app.include_router(notifications_router, prefix=f"{settings.API_V1_STR}/notifications", tags=["Notifications & Alerts"])
app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Executive Analytics"])
app.include_router(ml_status_router, prefix=f"{settings.API_V1_STR}/ml", tags=["ML Model Status"])

@app.get("/")
def root():
    resp = {
        "platform": settings.PROJECT_NAME,
        "status": "OPERATIONAL",
        "version": "1.0.0"
    }
    if (settings.ENVIRONMENT or "development").lower() != "production":
        resp["api_docs"] = f"{settings.API_V1_STR}/docs"
    return resp

@app.get("/health", status_code=200)
def health_check(db: Session = Depends(get_db)):
    """
    Lightweight, unauthenticated health check endpoint for container orchestrators and load balancers.
    Verifies application and database connectivity without leaking sensitive configuration or credentials.
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "UNHEALTHY", "database": "unavailable"}
        )
    return {
        "status": "HEALTHY",
        "database": "connected",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health/live", status_code=200)
def health_liveness():
    """
    Liveness probe: verifies that the application process is running.
    """
    return {
        "status": "ALIVE",
        "process": "running",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health/ready", status_code=200)
def health_readiness(db: Session = Depends(get_db)):
    """
    Readiness probe: verifies core operational dependencies while truthfully reporting
    component-level status (including simulated and fallback states without failing readiness).
    """
    # 1. Database check (mandatory for readiness)
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unavailable"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "NOT_READY",
                "application": "degraded",
                "database": "unavailable",
                "error": "Database connection failure"
            }
        )

    # 2. Model registry file check
    registry_file = Path(_PROJECT_ROOT) / "models" / "model_registry.json"
    registry_status = "available" if registry_file.exists() else "missing"

    # 3. Component truthful states
    components = {
        "application": "ready",
        "database": db_status,
        "authentication": "ready",
        "model_registry": registry_status,
        "demand": "trained",
        "maintenance": "trained",
        "energy": "trained",
        "enose": "trained (BEEF_QUALITY_ONLY)",
        "fruit_cv": "simulated (FRUIT_IMAGERY_ONLY, human_verification_required)",
        "waste": "fallback (0_production_waste_events)",
        "routing": "active (clarke_wright_2opt)"
    }

    return {
        "status": "READY",
        "environment": settings.ENVIRONMENT,
        "components": components
    }

# WebSockets Telemetry Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "event": "CONNECTED",
            "message": "Connected to reServe AI live sensory and redistribution event stream."
        }))
        while True:
            data = await websocket.receive_text()
            # Echo heartbeat or handle client commands
            await websocket.send_text(json.dumps({"event": "PONG", "payload": data}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
