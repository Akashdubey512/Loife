import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.core.config import settings
from backend.core.database import Base, engine
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables and seed data
    Base.metadata.create_all(bind=engine)
    try:
        seed_database()
    except Exception as e:
        print(f"Warning: Database seeding caught: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Enterprise AI-Powered Food Waste Reduction & Sustainable Redistribution Platform (SIH 2026)",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "status": "OPERATIONAL",
        "api_docs": f"{settings.API_V1_STR}/docs",
        "version": "1.0.0"
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
