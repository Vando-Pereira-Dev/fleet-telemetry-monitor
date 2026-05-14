from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ZONES
from app.db.models import Anomaly, Vehicle, ZoneEntryCount
from app.schemas.read_models import (
    AnomalyOut,
    FleetStatusCountsOut,
    FleetVehicleRow,
    FleetVehiclesSnapshotOut,
    LatestAnomalyBrief,
    ZoneCountOut,
    ZonesCountsOut,
)

VEHICLES_SNAPSHOT_SQL = text(
    """
    SELECT
      v.vehicle_id,
      v.current_status,
      v.battery_pct,
      v.last_event_ts,
      a.id AS anomaly_id,
      a.detected_at AS anomaly_detected_at,
      a.anomaly_type AS anomaly_type,
      a.detail AS anomaly_detail
    FROM vehicles v
    LEFT JOIN LATERAL (
      SELECT id, detected_at, anomaly_type, detail
      FROM anomalies an
      WHERE an.vehicle_id = v.vehicle_id
      ORDER BY an.detected_at DESC
      LIMIT 1
    ) a ON true
    ORDER BY v.vehicle_id
    """
)


async def fetch_vehicles_snapshot(session: AsyncSession) -> FleetVehiclesSnapshotOut:
    result = await session.execute(VEHICLES_SNAPSHOT_SQL)
    vehicles: list[FleetVehicleRow] = []
    for row in result.mappings().all():
        latest: LatestAnomalyBrief | None = None
        if row["anomaly_id"] is not None:
            latest = LatestAnomalyBrief(
                id=int(row["anomaly_id"]),
                detected_at=row["anomaly_detected_at"],
                anomaly_type=str(row["anomaly_type"]),
                detail=dict(row["anomaly_detail"] or {}),
            )
        vehicles.append(
            FleetVehicleRow(
                vehicle_id=str(row["vehicle_id"]),
                current_status=str(row["current_status"]),
                battery_pct=row["battery_pct"],
                last_event_ts=row["last_event_ts"],
                latest_anomaly=latest,
            )
        )
    return FleetVehiclesSnapshotOut(vehicles=vehicles)


async def fetch_zone_counts(session: AsyncSession) -> ZonesCountsOut:
    result = await session.execute(select(ZoneEntryCount.zone_id, ZoneEntryCount.entry_count))
    by_id = {row.zone_id: int(row.entry_count) for row in result.all()}
    zones = [ZoneCountOut(zone_id=z, entry_count=int(by_id.get(z, 0))) for z in ZONES]
    return ZonesCountsOut(zones=zones)


async def fetch_fleet_status_counts(session: AsyncSession) -> FleetStatusCountsOut:
    """Aggregate from `vehicles` (same implicit transaction = consistent MVCC snapshot)."""
    total_ct = await session.scalar(select(func.count()).select_from(Vehicle))
    stmt = select(Vehicle.current_status, func.count()).group_by(Vehicle.current_status)
    result = await session.execute(stmt)
    counts = {status: int(n) for status, n in result.all()}
    return FleetStatusCountsOut(
        idle=int(counts.get("idle", 0)),
        moving=int(counts.get("moving", 0)),
        charging=int(counts.get("charging", 0)),
        fault=int(counts.get("fault", 0)),
        total=int(total_ct or 0),
    )


async def fetch_anomalies(
    session: AsyncSession,
    *,
    vehicle_id: str | None,
    from_ts: datetime | None,
    to_ts: datetime | None,
    limit: int,
) -> list[AnomalyOut]:
    stmt = select(Anomaly).order_by(Anomaly.detected_at.desc())
    if vehicle_id is not None:
        stmt = stmt.where(Anomaly.vehicle_id == vehicle_id)
    if from_ts is not None:
        stmt = stmt.where(Anomaly.detected_at >= from_ts)
    if to_ts is not None:
        stmt = stmt.where(Anomaly.detected_at <= to_ts)
    stmt = stmt.limit(limit)
    result = await session.scalars(stmt)
    rows = result.all()
    return [AnomalyOut.model_validate(r) for r in rows]
