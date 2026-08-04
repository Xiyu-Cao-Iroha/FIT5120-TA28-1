import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class DataSource(Base):
    """Open-data source registry (FR-03)."""

    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    licence: Mapped[str] = mapped_column(String(200), nullable=False)
    refresh_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    sync_runs: Mapped[list["SyncRun"]] = relationship(back_populates="source")


class SyncRun(Base):
    """Synchronisation audit trail (FR-03)."""

    __tablename__ = "sync_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    source: Mapped[DataSource] = relationship(back_populates="sync_runs")

    __table_args__ = (
        CheckConstraint("status in ('running','success','failed')", name="ck_sync_runs_status"),
    )


class PedestrianSensor(Base):
    """Sensor locations (FR-03/FR-04)."""

    __tablename__ = "pedestrian_sensors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    external_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    geom = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    observations: Mapped[list["PedestrianObservation"]] = relationship(back_populates="sensor")

    __table_args__ = (Index("ix_pedestrian_sensors_geom", "geom", postgresql_using="gist"),)


class PedestrianObservation(Base):
    """Pedestrian count time series (FR-03/FR-04)."""

    __tablename__ = "pedestrian_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    sensor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pedestrian_sensors.id"), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    quality_flag: Mapped[str] = mapped_column(String(20), nullable=False, default="ok")
    sync_run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sync_runs.id"), nullable=True)

    sensor: Mapped[PedestrianSensor] = relationship(back_populates="observations")

    __table_args__ = (
        UniqueConstraint("sensor_id", "observed_at", name="uq_observation_sensor_time"),
        CheckConstraint("count >= 0", name="ck_observation_count_non_negative"),
        Index("ix_observation_sensor_time_desc", "sensor_id", observed_at.desc()),
    )


class Place(Base):
    """Landmarks / refuge candidates (Stretch, US 2.1)."""

    __tablename__ = "places"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source_external_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    geom = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    place_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (Index("ix_places_geom", "geom", postgresql_using="gist"),)


class ClassificationRule(Base):
    """Versioned sensory-classification configuration (FR-05)."""

    __tablename__ = "classification_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    version: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    crowd_score_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    min_data_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    max_observation_age_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "uq_classification_rules_single_active",
            "active",
            unique=True,
            postgresql_where=text("active"),
        ),
    )


class RouteRequest(Base):
    """Optional short-lived anonymous request audit (privacy: 24h retention target)."""

    __tablename__ = "route_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    origin_lat: Mapped[float] = mapped_column(Float, nullable=False)
    origin_lon: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lat: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lon: Mapped[float] = mapped_column(Float, nullable=False)
    snapshot_id: Mapped[str] = mapped_column(String(80), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    options: Mapped[list["RouteOption"]] = relationship(back_populates="request")


class RouteOption(Base):
    """Route comparison result (FR-02/FR-06)."""

    __tablename__ = "route_options"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("route_requests.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    duration_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    distance_meters: Mapped[float] = mapped_column(Float, nullable=False)
    geom = mapped_column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)
    crowd_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sensory_level: Mapped[str] = mapped_column(String(20), nullable=False)
    data_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    is_recommended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    explanation: Mapped[str] = mapped_column(String(500), nullable=False)

    request: Mapped[RouteRequest] = relationship(back_populates="options")
    segments: Mapped[list["RouteSegment"]] = relationship(back_populates="route")

    __table_args__ = (
        CheckConstraint(
            "sensory_level in ('low','high','unavailable')", name="ck_route_options_sensory_level"
        ),
    )


class RouteSegment(Base):
    """Explainable segment-level analysis (FR-04)."""

    __tablename__ = "route_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    route_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("route_options.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    geom = mapped_column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=False)
    crowd_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sensory_level: Mapped[str] = mapped_column(String(20), nullable=False)
    sensor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    route: Mapped[RouteOption] = relationship(back_populates="segments")

    __table_args__ = (Index("ix_route_segments_route_seq", "route_id", "sequence"),)
