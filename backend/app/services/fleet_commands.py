from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MaintenanceRecord, Mission, Vehicle


async def cancel_active_mission_and_record_maintenance(
    session: AsyncSession,
    *,
    vehicle_id: str,
    maintenance_reason: str,
) -> tuple[bool, uuid.UUID]:
    """Cancel at most one active mission and insert a maintenance row.

    Caller must already hold ``SELECT ... FOR UPDATE`` on the ``vehicles`` row
    for ``vehicle_id`` so this operation serializes with other per-vehicle writers.
    """
    mission = await session.scalar(
        select(Mission)
        .where(Mission.vehicle_id == vehicle_id, Mission.state == "active")
        .with_for_update(),
    )
    mission_id_for_record: uuid.UUID | None = None
    cancelled = False
    if mission is not None:
        mission.state = "cancelled"
        mission.cancelled_at = datetime.now(timezone.utc)
        mission_id_for_record = mission.id
        cancelled = True

    record = MaintenanceRecord(
        vehicle_id=vehicle_id,
        mission_id=mission_id_for_record,
        reason=maintenance_reason.strip(),
    )
    session.add(record)
    await session.flush()
    return cancelled, record.id


async def start_active_mission(session: AsyncSession, vehicle_id: str) -> Mission:
    vehicle = await session.get(Vehicle, vehicle_id, with_for_update=True)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown vehicle_id")

    existing = await session.scalar(
        select(Mission)
        .where(Mission.vehicle_id == vehicle_id, Mission.state == "active")
        .with_for_update(),
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active mission already exists for this vehicle",
        )

    mission = Mission(vehicle_id=vehicle_id, state="active")
    session.add(mission)
    await session.flush()
    return mission


async def apply_vehicle_status_update(
    session: AsyncSession,
    *,
    vehicle_id: str,
    new_status: str,
    maintenance_reason: str | None,
) -> tuple[str, bool, uuid.UUID | None]:
    """Apply a status change with fault-specific workflow.

    Returns ``(resulting_status, mission_cancelled, maintenance_record_id)``.
    """
    vehicle = await session.get(Vehicle, vehicle_id, with_for_update=True)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown vehicle_id")

    if new_status == "fault":
        if vehicle.current_status == "fault":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vehicle is already in fault state",
            )
        assert maintenance_reason is not None
        cancelled, maint_id = await cancel_active_mission_and_record_maintenance(
            session,
            vehicle_id=vehicle_id,
            maintenance_reason=maintenance_reason,
        )
        vehicle.current_status = "fault"
        return "fault", cancelled, maint_id

    vehicle.current_status = new_status
    return new_status, False, None
