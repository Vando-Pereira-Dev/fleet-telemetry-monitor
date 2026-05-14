from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Anomaly, TelemetryEvent, Vehicle, ZoneEntryCount
from app.schemas.telemetry import TelemetryCreate, TelemetryIngestResult
from app.services.anomaly_detection import _VehicleSnapshot, detect_telemetry_anomalies
from app.services.fleet_commands import cancel_active_mission_and_record_maintenance


async def ingest_telemetry(session: AsyncSession, payload: TelemetryCreate) -> TelemetryIngestResult:
    """Persist one telemetry event, update vehicle snapshot, optional zone count, anomalies.

    Locks: vehicle row then zone row (when present) to avoid deadlocks with other writers.
    """
    vehicle = await session.get(
        Vehicle,
        payload.vehicle_id,
        with_for_update=True,
    )
    if vehicle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown vehicle_id",
        )

    previous = _VehicleSnapshot(
        battery_pct=vehicle.battery_pct,
        last_event_ts=vehicle.last_event_ts,
    )

    event_row = TelemetryEvent(
        vehicle_id=payload.vehicle_id,
        event_ts=payload.event_ts,
        lat=payload.lat,
        lon=payload.lon,
        battery_pct=payload.battery_pct,
        speed_mps=payload.speed_mps,
        status=payload.status,
        error_codes=list(payload.error_codes),
        zone_entered=payload.zone_entered,
    )
    session.add(event_row)

    if payload.zone_entered is not None:
        zone = await session.get(
            ZoneEntryCount,
            payload.zone_entered,
            with_for_update=True,
        )
        if zone is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unknown zone_entered (not configured in zone_entry_counts)",
            )
        zone.entry_count += 1

    entering_fault = payload.status == "fault" and vehicle.current_status != "fault"
    if entering_fault:
        reason = (
            ", ".join(payload.error_codes)
            if payload.error_codes
            else "Fault reported via telemetry"
        )
        await cancel_active_mission_and_record_maintenance(
            session,
            vehicle_id=payload.vehicle_id,
            maintenance_reason=reason,
        )

    vehicle.current_status = payload.status
    vehicle.battery_pct = payload.battery_pct
    vehicle.speed_mps = payload.speed_mps
    vehicle.last_lat = payload.lat
    vehicle.last_lon = payload.lon
    vehicle.last_event_ts = payload.event_ts

    pairs = detect_telemetry_anomalies(payload, previous)
    for anomaly_type, detail in pairs:
        session.add(
            Anomaly(
                vehicle_id=payload.vehicle_id,
                detected_at=payload.event_ts,
                anomaly_type=anomaly_type,
                detail=detail,
            )
        )

    await session.flush()

    return TelemetryIngestResult(
        telemetry_event_id=int(event_row.id),
        anomalies_created=len(pairs),
    )
