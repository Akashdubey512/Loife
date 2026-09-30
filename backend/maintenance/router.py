from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.core.database import get_db
from backend.core.deps import get_current_user
from backend.models.entities import MachineEvent, User
from backend.schemas.sensors import MachineHealthOut

router = APIRouter()

class MachineEvaluateRequest(BaseModel):
    machine_id: str = "CHILLER-01"
    machine_type: str = "BLAST_CHILLER"
    air_temp_k: float = 300.0
    process_temp_k: float = 310.0
    rotational_speed_rpm: float = 1500.0
    torque_nm: float = 40.0
    tool_wear_min: float = 15.0

class MachineEvaluateResponse(BaseModel):
    machine_id: str
    machine_type: str
    failure_probability: float
    failure_type: str
    status: str
    power_w: float
    temp_diff_k: float
    recommended_action: str
    model_type: str
    model_version: str
    trained: bool
    fallback_used: bool
    dataset_benchmark: str

@router.get("/health", response_model=List[MachineHealthOut])
def get_equipment_health(
    kitchen_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    machines = db.query(MachineEvent).filter(MachineEvent.kitchen_id == kitchen_id).all()
    if machines:
        result = []
        for m in machines:
            rec = "Standard operation; regular inspection due in 15 days"
            if m.failure_probability > 0.6:
                rec = "URGENT: Schedule maintenance technician; compressor torque anomaly detected"
            elif m.failure_probability > 0.2:
                rec = "Inspect refrigerant pressure and heat exchanger fins"

            result.append(MachineHealthOut(
                machine_id=m.machine_id,
                machine_type=m.machine_type,
                failure_probability=m.failure_probability,
                failure_type=m.failure_type or "None",
                status=m.status,
                recommended_action=rec
            ))
        return result

    # Return realistic baseline machines
    return [
        MachineHealthOut(
            machine_id="CHILLER-ROOM-01",
            machine_type="BLAST_CHILLER",
            failure_probability=0.03,
            failure_type="None",
            status="HEALTHY",
            recommended_action="Optimal thermal cycle; next inspection in 21 days."
        ),
        MachineHealthOut(
            machine_id="STEAM-BOILER-02",
            machine_type="STEAM_BOILER",
            failure_probability=0.18,
            failure_type="Heat Dissipation Risk",
            status="MAINTENANCE_REQUIRED",
            recommended_action="Inspect steam pressure relief valve and descaling status."
        ),
        MachineHealthOut(
            machine_id="COMPRESSOR-UNIT-04",
            machine_type="REFRIGERATION_COMPRESSOR",
            failure_probability=0.05,
            failure_type="None",
            status="HEALTHY",
            recommended_action="Vibration and temperature profiles within standard tolerance."
        )
    ]

@router.post("/evaluate", response_model=MachineEvaluateResponse)
def evaluate_machine(
    request: MachineEvaluateRequest,
    current_user: User = Depends(get_current_user)
):
    """Evaluate machine health using trained ML model (AI4I 2020 dataset)."""
    from ml.predictive_maintenance import maintenance_engine
    result = maintenance_engine.evaluate_machine(
        machine_id=request.machine_id,
        machine_type=request.machine_type,
        air_temp_k=request.air_temp_k,
        process_temp_k=request.process_temp_k,
        rotational_speed_rpm=request.rotational_speed_rpm,
        torque_nm=request.torque_nm,
        tool_wear_min=request.tool_wear_min,
    )
    return MachineEvaluateResponse(**result)

