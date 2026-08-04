from dataclasses import dataclass

from app.schemas import SensoryLevel


@dataclass
class RouteCandidate:
    id: str
    name: str
    duration_minutes: float
    crowd_score: float | None
    sensory_level: SensoryLevel
    is_recommended: bool = False
    explanation: str = ""


def apply_recommendation(routes: list[RouteCandidate]) -> list[RouteCandidate]:
    """FR-06: recommend the valid route with the lowest crowd score.

    Selection is driven purely by crowd_score, never by duration, so a
    faster-but-more-congested route can never win over a slower-but-calmer
    one. Routes with unavailable sensory data are excluded from
    consideration entirely (FR-06: "must not receive a sensory-based
    recommendation").
    """
    eligible = [r for r in routes if r.sensory_level != SensoryLevel.unavailable and r.crowd_score is not None]

    if not eligible:
        for r in routes:
            r.is_recommended = False
            r.explanation = (
                "Sensory information unavailable for this route; no sensory-based "
                "recommendation could be made."
            )
        return routes

    winner = min(eligible, key=lambda r: r.crowd_score)
    all_congested = all(r.sensory_level == SensoryLevel.high for r in eligible)

    for r in routes:
        if r is winner:
            r.is_recommended = True
            if all_congested:
                r.explanation = (
                    "All compared routes currently show high pedestrian congestion. "
                    "This route has the comparatively lower congestion score, but it is "
                    "not congestion-free."
                )
            else:
                r.explanation = "Recommended for comparatively lower pedestrian congestion than the alternatives."
        elif r.sensory_level == SensoryLevel.unavailable:
            r.is_recommended = False
            r.explanation = "Sensory information unavailable for this route."
        else:
            r.is_recommended = False
            r.explanation = "Higher pedestrian congestion than the recommended route."
    return routes
