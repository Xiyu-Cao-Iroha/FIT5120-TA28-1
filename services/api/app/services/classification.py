from dataclasses import dataclass

from app.schemas import SensoryLevel


@dataclass(frozen=True)
class ClassificationRuleConfig:
    version: str
    crowd_score_threshold: float
    min_data_coverage: float
    max_observation_age_minutes: int


def classify(
    crowd_score: float | None, data_coverage: float, rule: ClassificationRuleConfig
) -> SensoryLevel:
    """FR-05: transparent, rule-based sensory classification.

    Unavailable takes precedence whenever coverage is insufficient or no
    crowd score could be computed at all - the system must never guess a
    level from partial or stale data (product principle 3.1).
    """
    if crowd_score is None or data_coverage < rule.min_data_coverage:
        return SensoryLevel.unavailable
    if crowd_score < rule.crowd_score_threshold:
        return SensoryLevel.low
    return SensoryLevel.high
