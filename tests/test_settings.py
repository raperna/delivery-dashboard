import pytest

from dashboard.config import (
    holiday_path,
    load_config,
    status_settings,
    validate_settings,
)


def base_settings():
    return status_settings(load_config())


def test_status_settings_come_from_project_config():
    assert base_settings() == {
        "midpoint_working_day": 5,
        "at_risk": 0.05,
        "off_track": 0.10,
        "max_defaulted_share": 0.20,
        "default_points": 1,
    }


def test_thresholds_must_be_ordered():
    with pytest.raises(ValueError):
        validate_settings(dict(base_settings(), at_risk=0.10, off_track=0.05))


def test_defaulted_share_must_be_a_fraction():
    with pytest.raises(ValueError):
        validate_settings(dict(base_settings(), max_defaulted_share=0))


def test_default_points_must_be_positive():
    with pytest.raises(ValueError):
        validate_settings(dict(base_settings(), default_points=0))


def test_holiday_source_exists():
    # Fails in CI if the fixture is moved or ignored by Git
    assert holiday_path(load_config()).exists()