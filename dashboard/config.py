from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_config(path=PROJECT_ROOT / "config.yaml"):
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def validate_settings(settings):
    """Reject values that would make the status rules meaningless (D-019, D-023)."""
    if not 0 < settings["at_risk"] < settings["off_track"] < 1:
        raise ValueError("thresholds must satisfy 0 < at_risk < off_track < 1")
    if not 0 < settings["max_defaulted_share"] < 1:
        raise ValueError("max_defaulted_share must be between 0 and 1")
    if settings["default_points"] <= 0:
        raise ValueError("default_points must be greater than 0")
    if settings["midpoint_working_day"] < 1:
        raise ValueError("midpoint_working_day must be at least 1")


def status_settings(config):
    """Collect the settings the status rules use, and validate them."""
    settings = {
        "midpoint_working_day": config["midpoint_working_day"],
        "at_risk": config["thresholds"]["at_risk"],
        "off_track": config["thresholds"]["off_track"],
        "max_defaulted_share": config["story_points"]["max_defaulted_share"],
        "default_points": config["story_points"]["default_points"],
    }
    validate_settings(settings)
    return settings


def holiday_path(config):
    """Resolve the holiday source relative to the project root."""
    return PROJECT_ROOT / config["holidays"]["source"]