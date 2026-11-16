from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def test_config_loads_and_has_required_sections():
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    assert config["sprint"]["length_working_days"] == 10
    assert config["thresholds"]["at_risk"] < config["thresholds"]["off_track"]
    assert config["midpoint_working_day"] < config["sprint"]["length_working_days"]
    assert "Blocked" in config["status_mapping"].values()