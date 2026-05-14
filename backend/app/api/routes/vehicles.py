from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.schemas.vehicles import MissionOut, VehicleStatusOut, VehicleStatusUpdate
from app.services.fleet_commands import (
    apply_vehicle_status_update,
    start_active_mission,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("/{vehicle_id}/status", response_model=VehicleStatusOut)
async def post_vehicle_status(
    vehicle_id: str,
    db: DbSession,
    body: VehicleStatusUpdate,
) -> VehicleStatusOut:
    async with db.begin():
        new_status, cancelled, maint_id = await apply_vehicle_status_update(
            db,
            vehicle_id=vehicle_id,
            new_status=body.status,
            maintenance_reason=body.maintenance_reason,
        )
    return VehicleStatusOut(
        vehicle_id=vehicle_id,
        current_status=new_status,
        mission_cancelled=cancelled,
        maintenance_record_id=maint_id,
    )


@router.post(
    "/{vehicle_id}/missions",
    response_model=MissionOut,
    status_code=status.HTTP_201_CREATED,
)
async def post_vehicle_mission(vehicle_id: str, db: DbSession) -> MissionOut:
    async with db.begin():
        mission = await start_active_mission(db, vehicle_id)
    return MissionOut.model_validate(mission)
