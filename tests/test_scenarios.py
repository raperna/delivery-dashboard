from datetime import date

import pytest

from dashboard.blocked import blocked_items
from dashboard.calendar import holidays_from_csv
from dashboard.config import holiday_path, load_config, status_settings
from dashboard.snapshot import team_report
from dashboard.synthetic import (
    BLOCKED,
    COLUMNS,
    DONE,
    END,
    EXPECTED_BLOCKED,
    EXPECTED_STATUS,
    SPRINT,
    START,
    TEAMS,
    build_scenario_events,
)

EVENTS = build_scenario_events()
HOLIDAYS = holidays_from_csv(holiday_path(load_config()))
SETTINGS = status_settings(load_config())


def test_generated_changelog_has_required_columns():
    assert list(EVENTS.columns) == COLUMNS


@pytest.mark.parametrize(
    "team, report_day, expected",
    [(team, report_day, status) for (team, report_day), status in EXPECTED_STATUS.items()],
)
def test_team_status_matches_hand_worked_answer(team, report_day, expected):
    result = team_report(
        EVENTS, SPRINT, START, END, report_day, team, TEAMS, DONE, HOLIDAYS, SETTINGS
    )
    assert result["status"] == expected


def test_blocked_list_matches_hand_worked_answer():
    rows = blocked_items(EVENTS, date(2026, 3, 6), BLOCKED, TEAMS)
    assert [(row["key"], row["team"], row["days_waiting"]) for row in rows] == EXPECTED_BLOCKED