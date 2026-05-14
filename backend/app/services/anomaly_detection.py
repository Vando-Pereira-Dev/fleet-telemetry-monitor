from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from app.schemas.telemetry import TelemetryCreate


@dataclass(frozen=True)
class _VehicleSnapshot:
    battery_pct: int | None
    last_event_ts: datetime | None


def detect_telemetry_anomalies(
    event: TelemetryCreate,
    previous: _VehicleSnapshot | None,
) -> list[tuple[str, dict[str, Any]]]:
    """Return (anomaly_type, detail_json) pairs for this telemetry event.

    Rules are deterministic and cheap to evaluate on the ingest hot path.
    """
    out: list[tuple[str, dict[str, Any]]] = []

    if event.error_codes:
        out.append(
            (
                "ERROR_CODES_PRESENT",
                {"error_codes": list(event.error_codes)},
            )
        )

    if event.status == "fault":
        out.append(("FAULT_STATUS", {"status": event.status}))

    if event.battery_pct <= 10:
        out.append(
            (
                "CRITICAL_LOW_BATTERY",
                {"battery_pct": event.battery_pct},
            )
        )

    if event.status == "idle" and event.speed_mps > 0.15:
        out.append(
            (
                "IDLE_WITH_SPEED",
                {"speed_mps": event.speed_mps, "status": event.status},
            )
        )

    if previous is not None and previous.battery_pct is not None and previous.last_event_ts is not None:
        delta_t = event.event_ts - previous.last_event_ts
        if timedelta(0) <= delta_t <= timedelta(seconds=90):
            drop = previous.battery_pct - event.battery_pct
            if drop >= 12:
                out.append(
                    (
                        "RAPID_BATTERY_DROP",
                        {
                            "previous_battery_pct": previous.battery_pct,
                            "battery_pct": event.battery_pct,
                            "seconds": delta_t.total_seconds(),
                        },
                    )
                )

    return out
