from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ZoneCountOut(BaseModel):
    zone_id: str
    entry_count: int


class ZonesCountsOut(BaseModel):
    zones: list[ZoneCountOut]


class FleetStatusCountsOut(BaseModel):
    """Per-status vehicle counts; each field is the number of vehicles in that status."""

    idle: int = 0
    moving: int = 0
    charging: int = 0
    fault: int = 0
    total: int


class AnomalyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: str
    detected_at: datetime
    anomaly_type: str
    detail: dict[str, Any]
