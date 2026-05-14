from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.read_models import FleetStatusCountsOut
from app.services.read_queries import fetch_fleet_status_counts

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.get("/state", response_model=FleetStatusCountsOut)
async def get_fleet_state(db: DbSession) -> FleetStatusCountsOut:
    return await fetch_fleet_status_counts(db)
