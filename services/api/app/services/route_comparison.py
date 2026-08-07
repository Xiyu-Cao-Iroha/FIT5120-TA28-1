import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import Settings
from app.schemas import CongestedSegment, CrowdSensitivity, RouteCompareResponse, RouteOptionOut
from app.services.classification import ClassificationRuleConfig, classify
from app.services.melbourne_open_data import MelbourneOpenDataPedestrianRepository
from app.services.pedestrian_repository import PedestrianDataRepository
from app.services.recommendation import RouteCandidate, apply_recommendation
from app.services.routing_adapter import RoutingProvider

# US 1.3 (prototype-only, requirements section 15): a crowd-sensitivity
# preference scales the classification threshold for this request only -
# it never mutates the stored classification_rules row. Someone with
# "high" sensitivity wants stricter flagging (lower threshold => more
# routes read as High); "low" sensitivity tolerates more crowding before a
# route is called High.
CROWD_SENSITIVITY_THRESHOLD_MULTIPLIER: dict[CrowdSensitivity, float] = {
    CrowdSensitivity.low: 1.25,
    CrowdSensitivity.moderate: 1.0,
    CrowdSensitivity.high: 0.65,
}


def _linestring_wkt(polyline: list[tuple[float, float]]) -> str:
    coords = ", ".join(f"{lon} {lat}" for lat, lon in polyline)
    return f"LINESTRING({coords})"


def _demo_sensor_prefix(origin: tuple[float, float], destination: tuple[float, float]) -> str | None:
    """If (origin, destination) is one of seed.py's pinned demo scenarios,
    scope sensor matching to that scenario's own sensors only. Several demo
    scenarios' real Google-routed streets overlap in the compact CBD (most
    share stretches of Swanston St); without this, a busy scenario's
    sensors leak into an unrelated scenario's route and defeat the
    intended Low/High contrast."""
    from app.seed import DEMO_SCENARIO_KEY_BY_PAIR
    from app.services.route_snapshot_cache import route_pair_key

    key = DEMO_SCENARIO_KEY_BY_PAIR.get(route_pair_key(origin, destination))
    return f"demo-{key}-" if key else None


def compare_routes(
    db: Session,
    settings: Settings,
    routing_provider: RoutingProvider,
    origin: tuple[float, float],
    destination: tuple[float, float],
    crowd_sensitivity: CrowdSensitivity | None = None,
) -> RouteCompareResponse:
    """Orchestrates FR-02 (routing) + FR-04 (matching) + FR-05
    (classification) + FR-06 (recommendation) into one comparison response.
    All routes in one response share the same snapshot id and rule version
    (FR-02: "same data snapshot and classification-rule version")."""
    now = datetime.now(timezone.utc)
    multiplier = CROWD_SENSITIVITY_THRESHOLD_MULTIPLIER[crowd_sensitivity] if crowd_sensitivity else 1.0
    rule = ClassificationRuleConfig(
        version=settings.default_rule_version,
        crowd_score_threshold=min(1.0, settings.default_crowd_score_threshold * multiplier),
        min_data_coverage=settings.default_min_data_coverage,
        max_observation_age_minutes=settings.default_max_observation_age_minutes,
    )
    sensor_prefix = _demo_sensor_prefix(origin, destination)
    if sensor_prefix is None and settings.use_live_pedestrian_data:
        # Pinned demo pairs never take this path, even with the flag on -
        # they must stay reliable for a presentation regardless of the City
        # of Melbourne API's availability or the network at demo time.
        repo = MelbourneOpenDataPedestrianRepository(
            settings.sensor_match_radius_meters,
            rule.max_observation_age_minutes,
            cbd_bounds=(settings.cbd_min_lat, settings.cbd_max_lat, settings.cbd_min_lon, settings.cbd_max_lon),
            timeout_seconds=settings.melbourne_open_data_timeout_seconds,
        )
    else:
        repo = PedestrianDataRepository(db, settings.sensor_match_radius_meters, rule.max_observation_age_minutes)

    candidates = routing_provider.get_candidate_routes(origin, destination)
    snapshot_id = f"snap-{now.strftime('%Y%m%dT%H%M%S')}"

    built_routes: list[RouteOptionOut] = []
    reco_candidates: list[RouteCandidate] = []

    for candidate in candidates:
        segment_stats = [
            repo.stats_for_segment(seg.polyline, now, sensor_external_id_prefix=sensor_prefix)
            for seg in candidate.segments
        ]

        covered = sum(1 for s in segment_stats if s.has_coverage)
        data_coverage = covered / len(segment_stats) if segment_stats else 0.0

        scored = [s.crowd_score for s in segment_stats if s.crowd_score is not None]
        # Route score = average of its (near-equal-length) segment scores.
        # Individual congested blocks are still surfaced via
        # congested_segments below (AC 1.2.1); averaging here keeps the
        # overall route classification from being dominated by a single
        # segment near the shared origin/destination that two candidate
        # routes both pass close to.
        route_crowd_score = (sum(scored) / len(scored)) if scored else None

        sensory_level = classify(route_crowd_score, data_coverage, rule)

        congested_segments = [
            CongestedSegment(
                sequence=seg.sequence,
                geometry=_linestring_wkt(seg.polyline),
                crowd_score=stats.crowd_score,
                sensory_level=classify(stats.crowd_score, 1.0, rule),
            )
            for seg, stats in zip(candidate.segments, segment_stats)
            if stats.crowd_score is not None and stats.crowd_score >= rule.crowd_score_threshold
        ]

        built_routes.append(
            RouteOptionOut(
                id=candidate.id,
                name=candidate.name,
                duration_minutes=candidate.duration_minutes,
                distance_meters=candidate.distance_meters,
                geometry=_linestring_wkt(candidate.polyline),
                sensory_level=sensory_level,
                crowd_score=route_crowd_score,
                data_coverage=round(data_coverage, 2),
                is_recommended=False,
                explanation="",
                congested_segments=congested_segments,
                data_updated_at=now if scored else None,
                rule_version=rule.version,
            )
        )
        reco_candidates.append(
            RouteCandidate(
                id=candidate.id,
                name=candidate.name,
                duration_minutes=candidate.duration_minutes,
                crowd_score=route_crowd_score,
                sensory_level=sensory_level,
            )
        )

    decided_by_id = {d.id: d for d in apply_recommendation(reco_candidates)}
    for route_out in built_routes:
        decision = decided_by_id[route_out.id]
        route_out.is_recommended = decision.is_recommended
        route_out.explanation = decision.explanation

    return RouteCompareResponse(
        request_id=str(uuid.uuid4()),
        snapshot_id=snapshot_id,
        rule_version=rule.version,
        routes=built_routes,
    )
