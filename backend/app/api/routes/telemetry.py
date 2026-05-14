from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.schemas.telemetry import TelemetryCreate, TelemetryIngestResult
from app.services.telemetry_ingest import ingest_telemetry

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post(
    "",
    response_model=TelemetryIngestResult,
    status_code=status.HTTP_201_CREATED,
)
async def post_telemetry(db: DbSession, body: TelemetryCreate) -> TelemetryIngestResult:
    async with db.begin():
        return await ingest_telemetry(db, body)
