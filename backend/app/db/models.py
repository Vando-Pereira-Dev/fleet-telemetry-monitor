import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    current_status: Mapped[str] = mapped_column(String(32), nullable=False, default="idle")
    battery_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speed_mps: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_event_ts: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    telemetry_events: Mapped[list["TelemetryEvent"]] = relationship(back_populates="vehicle")
    anomalies: Mapped[list["Anomaly"]] = relationship(back_populates="vehicle")
    missions: Mapped[list["Mission"]] = relationship(back_populates="vehicle")
    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(back_populates="vehicle")


class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"
    __table_args__ = (
        Index("ix_telemetry_vehicle_event_ts", "vehicle_id", "event_ts"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        nullable=False,
    )
    event_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    battery_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    speed_mps: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error_codes: Mapped[list[Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    zone_entered: Mapped[str | None] = mapped_column(String(128), nullable=True)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="telemetry_events")


class Anomaly(Base):
    __tablename__ = "anomalies"
    __table_args__ = (
        Index("ix_anomaly_vehicle_detected_at", "vehicle_id", "detected_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        nullable=False,
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    anomaly_type: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    vehicle: Mapped["Vehicle"] = relationship(back_populates="anomalies")


class Mission(Base):
    __tablename__ = "missions"
    __table_args__ = (
        Index(
            "ix_missions_one_active_per_vehicle",
            "vehicle_id",
            unique=True,
            postgresql_where=text("state = 'active'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    vehicle_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        nullable=False,
    )
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="missions")
    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(back_populates="mission")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    vehicle_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"),
        nullable=False,
    )
    mission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("missions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    vehicle: Mapped["Vehicle"] = relationship(back_populates="maintenance_records")
    mission: Mapped["Mission | None"] = relationship(back_populates="maintenance_records")


class ZoneEntryCount(Base):
    __tablename__ = "zone_entry_counts"

    zone_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    entry_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
