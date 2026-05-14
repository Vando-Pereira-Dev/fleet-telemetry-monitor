from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import VEHICLE_STATUS_VALUES, ZONES


class TelemetryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    vehicle_id: str
    event_ts: datetime = Field(
        ...,
        validation_alias="timestamp",
        serialization_alias="timestamp",
    )
    lat: float
    lon: float
    battery_pct: int
    speed_mps: float
    status: str
    error_codes: list[str] = Field(default_factory=list)
    zone_entered: str | None = None

    @field_validator("status")
    @classmethod
    def status_must_be_known(cls, v: str) -> str:
        if v not in VEHICLE_STATUS_VALUES:
            allowed = ", ".join(VEHICLE_STATUS_VALUES)
            raise ValueError(f"status must be one of: {allowed}")
        return v

    @field_validator("battery_pct")
    @classmethod
    def battery_in_range(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError("battery_pct must be between 0 and 100")
        return v

    @field_validator("speed_mps")
    @classmethod
    def speed_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("speed_mps must be non-negative")
        return v

    @field_validator("zone_entered")
    @classmethod
    def zone_must_be_known_if_set(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if v not in ZONES:
            raise ValueError("zone_entered must be a known zone id or null")
        return v


class TelemetryIngestResult(BaseModel):
    telemetry_event_id: int
    anomalies_created: int
