from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.schemas.read_models import AnomalyOut
from app.services.read_queries import fetch_anomalies

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyOut])
async def list_anomalies(
    db: DbSession,
    vehicle_id: str | None = Query(
        default=None,
        description="Filter to a single vehicle id (e.g. v-12).",
    ),
    from_ts: datetime | None = Query(
        default=None,
        description="Inclusive lower bound on detected_at (ISO-8601).",
    ),
    to_ts: datetime | None = Query(
        default=None,
        description="Inclusive upper bound on detected_at (ISO-8601).",
    ),
    limit: int = Query(default=200, ge=1, le=2000),
) -> list[AnomalyOut]:
    if from_ts is not None and to_ts is not None and from_ts > to_ts:
        raise HTTPException(
            status_code=400,
            detail="from_ts must be less than or equal to to_ts",
        )
    return await fetch_anomalies(
        db,
        vehicle_id=vehicle_id,
        from_ts=from_ts,
        to_ts=to_ts,
        limit=limit,
    )
