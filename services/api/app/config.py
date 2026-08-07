from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration.

    All classification/service-boundary values live here (not hard-coded)
    per FR-05's requirement that thresholds be stored as configuration.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://calmpath:calmpath@localhost:5432/calmpath"
    cors_origins: str = "http://localhost:8081,http://localhost:19006"

    # Melbourne CBD service boundary (bounding box placeholder pending
    # section 20 decision #1 - formal boundary confirmation).
    cbd_min_lat: float = -37.8230
    cbd_max_lat: float = -37.8050
    cbd_min_lon: float = 144.9400
    cbd_max_lon: float = 144.9700

    # Active classification rule defaults (see classification_rules table;
    # DB-stored config overrides these once seeded).
    default_rule_version: str = "v1"
    default_crowd_score_threshold: float = 0.6
    default_min_data_coverage: float = 0.5
    default_max_observation_age_minutes: int = 30
    sensor_match_radius_meters: float = 75.0

    rate_limit_per_minute: int = 10

    # FR-02/FR-09 decision #3+#4 (section 20): when unset, routing and place
    # search fall back to the demo/gazetteer providers rather than failing -
    # set this to switch both over to Google Maps Platform without any other
    # code change.
    google_maps_api_key: str | None = None
    google_maps_request_timeout_seconds: float = 8.0

    # FR-03/FR-09: when true, (a) non-demo route comparisons fetch live
    # pedestrian crowd data from the City of Melbourne open data portal
    # instead of the seeded PedestrianDataRepository, and (b) `python -m
    # app.seed` refreshes real quiet-place landmarks (libraries, galleries/
    # museums, places of worship) from the same portal alongside the hand
    # curated demo refuges. No API key needed - it's all public. Pinned demo
    # scenarios always use seeded pedestrian data regardless of this flag -
    # see route_comparison.py. Off by default so a fresh clone works without
    # network access; enable explicitly once you want live data.
    use_live_melbourne_open_data: bool = False
    melbourne_open_data_timeout_seconds: float = 8.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
