from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.read_models import ZonesCountsOut
from app.services.read_queries import fetch_zone_counts

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("/counts", response_model=ZonesCountsOut)
async def get_zone_counts(db: DbSession) -> ZonesCountsOut:
    return await fetch_zone_counts(db)
