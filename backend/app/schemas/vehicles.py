from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class VehicleStatusUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    status: Literal["idle", "moving", "charging", "fault"]
    maintenance_reason: str | None = Field(
        default=None,
        description="Required when status is fault (free-text for maintenance systems).",
    )

    @model_validator(mode="after")
    def fault_requires_reason(self) -> VehicleStatusUpdate:
        if self.status == "fault":
            if self.maintenance_reason is None or not self.maintenance_reason.strip():
                raise ValueError("maintenance_reason is required when status is fault")
        return self


class VehicleStatusOut(BaseModel):
    vehicle_id: str
    current_status: str
    mission_cancelled: bool
    maintenance_record_id: uuid.UUID | None = None


class MissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vehicle_id: str
    state: str
