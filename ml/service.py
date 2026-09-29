"""
reServe AI - ML Service Microservice
Exposes demand forecasting, waste prediction, predictive maintenance, and sustainability APIs.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
from typing import List, Optional

from ml.demand_forecast import demand_engine
from ml.waste_predictor import waste_engine
from ml.sustainability_engine import sustainability_engine
from ml.predictive_maintenance import maintenance_engine

app = FastAPI(title="reServe AI - Machine Learning Microservice", version="1.0.0")

class DemandRequest(BaseModel):
    center_id: int
    meal_id: int
    target_date: date
    base_price: float = 120.0
    checkout_price: float = 110.0
    historical_demands: Optional[List[float]] = None

class WasteRequest(BaseModel):
    production_kg: float
    expected_demand_kg: float
    inventory_batches_near_expiry_kg: float
    historical_waste_rate: float = 0.06

class MachineHealthRequest(BaseModel):
    machine_id: str
    machine_type: str
    air_temp_k: float = 300.0
    process_temp_k: float = 310.0
    rotational_speed_rpm: float = 1500.0
    torque_nm: float = 40.0
    tool_wear_min: float = 15.0

class SustainabilityRequest(BaseModel):
    category: str
    quantity_kg: float

@app.get("/")
def health():
    return {"status": "ML_SERVICES_ONLINE"}

@app.post("/predict/demand")
def predict_demand(req: DemandRequest):
    return demand_engine.predict(
        center_id=req.center_id,
        meal_id=req.meal_id,
        target_date=req.target_date,
        base_price=req.base_price,
        checkout_price=req.checkout_price,
        historical_demands=req.historical_demands
    )

@app.post("/predict/waste")
def predict_waste(req: WasteRequest):
    return waste_engine.predict_waste(
        production_kg=req.production_kg,
        expected_demand_kg=req.expected_demand_kg,
        inventory_batches_near_expiry_kg=req.inventory_batches_near_expiry_kg,
        historical_waste_rate=req.historical_waste_rate
    )

@app.post("/predict/maintenance")
def predict_maintenance(req: MachineHealthRequest):
    return maintenance_engine.evaluate_machine(
        machine_id=req.machine_id,
        machine_type=req.machine_type,
        air_temp_k=req.air_temp_k,
        process_temp_k=req.process_temp_k,
        rotational_speed_rpm=req.rotational_speed_rpm,
        torque_nm=req.torque_nm,
        tool_wear_min=req.tool_wear_min
    )

@app.post("/calculate/sustainability")
def calc_sustainability(req: SustainabilityRequest):
    return sustainability_engine.calculate_impact(
        category=req.category,
        quantity_kg=req.quantity_kg
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
