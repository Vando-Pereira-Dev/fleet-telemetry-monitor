"""Initial schema and seed data (50 vehicles, 20 zones).

Revision ID: 001_initial
Revises:
Create Date: 2026-05-14

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ZONES_SEED = [
    "inbound_dock_a",
    "inbound_dock_b",
    "receiving_staging",
    "aisle_a",
    "aisle_b",
    "aisle_c",
    "high_bay_1",
    "high_bay_2",
    "bulk_storage",
    "pick_zone_1",
    "pick_zone_2",
    "pack_station",
    "sort_belt",
    "outbound_dock_a",
    "outbound_dock_b",
    "shipping_staging",
    "charging_bay_1",
    "charging_bay_2",
    "charging_bay_3",
    "maintenance_bay",
]


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("vehicle_id", sa.String(length=64), nullable=False),
        sa.Column("current_status", sa.String(length=32), nullable=False),
        sa.Column("battery_pct", sa.Integer(), nullable=True),
        sa.Column("speed_mps", sa.Float(), nullable=True),
        sa.Column("last_lat", sa.Float(), nullable=True),
        sa.Column("last_lon", sa.Float(), nullable=True),
        sa.Column("last_event_ts", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("vehicle_id"),
    )

    op.create_table(
        "zone_entry_counts",
        sa.Column("zone_id", sa.String(length=128), nullable=False),
        sa.Column(
            "entry_count",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("zone_id"),
    )

    op.create_table(
        "missions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("vehicle_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_missions_one_active_per_vehicle",
        "missions",
        ["vehicle_id"],
        unique=True,
        postgresql_where=sa.text("state = 'active'"),
    )

    op.create_table(
        "telemetry_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("vehicle_id", sa.String(length=64), nullable=False),
        sa.Column("event_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("battery_pct", sa.Integer(), nullable=False),
        sa.Column("speed_mps", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "error_codes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("zone_entered", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_telemetry_vehicle_event_ts",
        "telemetry_events",
        ["vehicle_id", "event_ts"],
        unique=False,
    )

    op.create_table(
        "anomalies",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("vehicle_id", sa.String(length=64), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("anomaly_type", sa.String(length=64), nullable=False),
        sa.Column(
            "detail",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_anomaly_vehicle_detected_at",
        "anomalies",
        ["vehicle_id", "detected_at"],
        unique=False,
    )

    op.create_table(
        "maintenance_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("vehicle_id", sa.String(length=64), nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    vehicles_t = sa.table(
        "vehicles",
        sa.column("vehicle_id", sa.String()),
        sa.column("current_status", sa.String()),
    )
    op.bulk_insert(
        vehicles_t,
        [{"vehicle_id": f"v-{i}", "current_status": "idle"} for i in range(1, 51)],
    )

    zones_t = sa.table(
        "zone_entry_counts",
        sa.column("zone_id", sa.String()),
        sa.column("entry_count", sa.BigInteger()),
    )
    op.bulk_insert(
        zones_t,
        [{"zone_id": z, "entry_count": 0} for z in ZONES_SEED],
    )


def downgrade() -> None:
    op.drop_table("maintenance_records")
    op.drop_table("anomalies")
    op.drop_table("telemetry_events")
    op.drop_table("missions")
    op.drop_table("zone_entry_counts")
    op.drop_table("vehicles")
