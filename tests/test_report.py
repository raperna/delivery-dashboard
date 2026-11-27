from datetime import date

from dashboard.report import build_report, sprint_names

from dashboard.calendar import holidays_from_csv
from dashboard.config import (
    holiday_path,
    load_config,
    status_settings,
    statuses_mapped_to,
)
from dashboard.synthetic import (
    END,
    EXPECTED_BLOCKED,
    EXPECTED_STATUS,
    SPRINT,
    START,
    TEAMS,
    build_scenario_events,
)

EVENTS = build_scenario_events()
CONFIG = load_config()
HOLIDAYS = holidays_from_csv(holiday_path(CONFIG))
SETTINGS = status_settings(CONFIG)
DONE = statuses_mapped_to(CONFIG, "Done")
BLOCKED = statuses_mapped_to(CONFIG, "Blocked")
REPORT_DAY = date(2026, 3, 6)


def build(report_day=REPORT_DAY, team_labels=TEAMS):
    return build_report(
        EVENTS, SPRINT, START, END, report_day, team_labels, DONE, BLOCKED, HOLIDAYS, SETTINGS
    )


def test_sprint_names_lists_every_sprint_seen():
    assert sprint_names(EVENTS) == ["Sprint 29"]


def test_report_gives_elapsed_and_sprint_days():
    report = build()
    assert report["elapsed_days"] == 5
    assert report["sprint_days"] == 10


def test_one_row_per_configured_team():
    report = build()
    assert [row["team"] for row in report["teams"]] == TEAMS


def test_team_statuses_match_hand_worked_answers():
    expected = {
        team: status
        for (team, day), status in EXPECTED_STATUS.items()
        if day == REPORT_DAY
    }
    actual = {row["team"]: row["status"] for row in build()["teams"]}
    assert {team: actual[team] for team in expected} == expected


def test_team_with_no_committed_items_is_not_assessed():
    report = build(team_labels=TEAMS + ["Mobile"])
    mobile = next(row for row in report["teams"] if row["team"] == "Mobile")
    assert mobile["status"] == "Not assessed"


def test_blocked_section_matches_hand_worked_answer():
    rows = build()["blocked"]
    assert [(row["key"], row["team"], row["days_waiting"]) for row in rows] == EXPECTED_BLOCKED