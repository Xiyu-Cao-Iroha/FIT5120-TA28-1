"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-04
"""
from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "data_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("licence", sa.String(200), nullable=False),
        sa.Column("refresh_interval_minutes", sa.Integer, nullable=False, server_default="60"),
    )

    op.create_table(
        "sync_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("row_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error", sa.String(2000), nullable=True),
        sa.CheckConstraint("status in ('running','success','failed')", name="ck_sync_runs_status"),
    )

    op.create_table(
        "pedestrian_sensors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(120), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("geom", geoalchemy2.Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "ix_pedestrian_sensors_geom", "pedestrian_sensors", ["geom"], postgresql_using="gist"
    )

    op.create_table(
        "pedestrian_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "sensor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pedestrian_sensors.id"),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("count", sa.Integer, nullable=False),
        sa.Column("interval_minutes", sa.Integer, nullable=False, server_default="15"),
        sa.Column("quality_flag", sa.String(20), nullable=False, server_default="ok"),
        sa.Column("sync_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sync_runs.id"), nullable=True),
        sa.UniqueConstraint("sensor_id", "observed_at", name="uq_observation_sensor_time"),
        sa.CheckConstraint("count >= 0", name="ck_observation_count_non_negative"),
    )
    op.create_index(
        "ix_observation_sensor_time_desc",
        "pedestrian_observations",
        ["sensor_id", sa.text("observed_at DESC")],
    )

    op.create_table(
        "places",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_external_id", sa.String(120), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("address", sa.String(300), nullable=True),
        sa.Column("geom", geoalchemy2.Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("place_metadata", postgresql.JSONB, nullable=True),
    )
    op.create_index("ix_places_geom", "places", ["geom"], postgresql_using="gist")

    op.create_table(
        "classification_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.String(40), nullable=False, unique=True),
        sa.Column("crowd_score_threshold", sa.Float, nullable=False),
        sa.Column("min_data_coverage", sa.Float, nullable=False),
        sa.Column("max_observation_age_minutes", sa.Integer, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "uq_classification_rules_single_active",
        "classification_rules",
        ["active"],
        unique=True,
        postgresql_where=sa.text("active = true"),
    )

    op.create_table(
        "route_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("origin_lat", sa.Float, nullable=False),
        sa.Column("origin_lon", sa.Float, nullable=False),
        sa.Column("destination_lat", sa.Float, nullable=False),
        sa.Column("destination_lon", sa.Float, nullable=False),
        sa.Column("snapshot_id", sa.String(80), nullable=False),
        sa.Column("rule_version", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "route_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("route_requests.id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("duration_minutes", sa.Float, nullable=False),
        sa.Column("distance_meters", sa.Float, nullable=False),
        sa.Column("geom", geoalchemy2.Geometry(geometry_type="LINESTRING", srid=4326), nullable=False),
        sa.Column("crowd_score", sa.Float, nullable=True),
        sa.Column("sensory_level", sa.String(20), nullable=False),
        sa.Column("data_coverage", sa.Float, nullable=False),
        sa.Column("is_recommended", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("explanation", sa.String(500), nullable=False),
        sa.CheckConstraint(
            "sensory_level in ('low','high','unavailable')", name="ck_route_options_sensory_level"
        ),
    )

    op.create_table(
        "route_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("route_options.id"), nullable=False),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("geom", geoalchemy2.Geometry(geometry_type="LINESTRING", srid=4326), nullable=False),
        sa.Column("crowd_score", sa.Float, nullable=True),
        sa.Column("sensory_level", sa.String(20), nullable=False),
        sa.Column("sensor_count", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_route_segments_route_seq", "route_segments", ["route_id", "sequence"])


def downgrade() -> None:
    op.drop_table("route_segments")
    op.drop_table("route_options")
    op.drop_table("route_requests")
    op.drop_index("uq_classification_rules_single_active", table_name="classification_rules")
    op.drop_table("classification_rules")
    op.drop_index("ix_places_geom", table_name="places")
    op.drop_table("places")
    op.drop_index("ix_observation_sensor_time_desc", table_name="pedestrian_observations")
    op.drop_table("pedestrian_observations")
    op.drop_index("ix_pedestrian_sensors_geom", table_name="pedestrian_sensors")
    op.drop_table("pedestrian_sensors")
    op.drop_table("sync_runs")
    op.drop_table("data_sources")
