from app.schemas import SensoryLevel
from app.services.classification import ClassificationRuleConfig, classify

RULE = ClassificationRuleConfig(
    version="v1", crowd_score_threshold=0.6, min_data_coverage=0.5, max_observation_age_minutes=30
)


def test_below_threshold_is_low():
    assert classify(0.59, 1.0, RULE) == SensoryLevel.low


def test_equal_to_threshold_is_high():
    assert classify(0.6, 1.0, RULE) == SensoryLevel.high


def test_above_threshold_is_high():
    assert classify(0.61, 1.0, RULE) == SensoryLevel.high


def test_coverage_just_below_minimum_is_unavailable():
    assert classify(0.1, 0.49, RULE) == SensoryLevel.unavailable


def test_coverage_exactly_at_minimum_is_classified_normally():
    assert classify(0.1, 0.5, RULE) == SensoryLevel.low


def test_missing_crowd_score_is_unavailable():
    assert classify(None, 1.0, RULE) == SensoryLevel.unavailable


def test_missing_score_and_low_coverage_is_still_unavailable():
    assert classify(None, 0.0, RULE) == SensoryLevel.unavailable
