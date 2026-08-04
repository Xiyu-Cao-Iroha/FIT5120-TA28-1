from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SensoryLevel(str, Enum):
    low = "low"
    high = "high"
    unavailable = "unavailable"


class CrowdSensitivity(str, Enum):
    """US 1.3 (prototype-only, requirements section 15): a selected crowd-
    sensitivity preference shifts the classification threshold used for
    this request only - it does not change the stored default rule."""

    low = "low"
    moderate = "moderate"
    high = "high"


class LatLon(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class RouteCompareRequest(BaseModel):
    origin: LatLon
    destination: LatLon
    crowd_sensitivity: CrowdSensitivity | None = None


class CongestedSegment(BaseModel):
    sequence: int
    geometry: str
    crowd_score: float | None
    sensory_level: SensoryLevel


class RouteOptionOut(BaseModel):
    id: str
    name: str
    duration_minutes: float
    distance_meters: float
    geometry: str
    sensory_level: SensoryLevel
    crowd_score: float | None
    data_coverage: float
    is_recommended: bool
    explanation: str
    congested_segments: list[CongestedSegment]
    data_updated_at: datetime | None
    rule_version: str


class RouteCompareResponse(BaseModel):
    request_id: str
    snapshot_id: str
    rule_version: str
    routes: list[RouteOptionOut]


class RouteDetailResponse(RouteOptionOut):
    pass


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthComponent(BaseModel):
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    api: HealthComponent
    database: HealthComponent
    data_freshness: HealthComponent


class RefugeSource(str, Enum):
    """Product principle 14.2: refuge locations must be described
    conservatively and supported by source data - the client renders this
    distinction rather than presenting every candidate as equally verified."""

    verified = "verified"
    prototype = "prototype"


class RefugeSummary(BaseModel):
    id: str
    name: str
    category: str
    address: str
    lat: float
    lon: float
    distance_meters: float
    short_description: str
    data_source: RefugeSource


class RefugeListResponse(BaseModel):
    route_id: str
    refuges: list[RefugeSummary]


class RefugeDetail(RefugeSummary):
    facility_info: str
    source_note: str


class PlaceSuggestion(BaseModel):
    place_id: str
    description: str


class PlaceSearchResponse(BaseModel):
    suggestions: list[PlaceSuggestion]


class ResolvedPlace(BaseModel):
    place_id: str
    description: str
    lat: float
    lon: float
