from datetime import date

import pandas as pd

from dashboard.calendar import holidays_from_csv
from dashboard.config import (
    holiday_path,
    load_config,
    status_settings,
    statuses_mapped_to,
)
from dashboard.report import build_report
from dashboard.signals import scope_changes, team_facts, where_to_look
from dashboard.synthetic import END as SCENARIO_END
from dashboard.synthetic import SPRINT as SCENARIO_SPRINT
from dashboard.synthetic import START as SCENARIO_START
from dashboard.synthetic import build_scenario_events

TEAMS = ["Backend", "Frontend", "DevOps", "QA"]
DONE = {"Done"}
BLOCKED = {"Blocked"}
START = date(2026, 3, 2)
REPORT = date(2026, 3, 6)
COLUMNS = ["key", "created", "field", "fromString", "toString"]
NO_SCOPE = {"added": {"count": 0, "points": 0}, "removed": {"count": 0, "points": 0}}
FACTS = {
    "committed_points": 10, "blank_items": 0, "committed_items": 10,
    "open_items": 0, "open_developers": 0, "unassigned_open": 0, "blocked_items": 0,
}


def make_events(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def joins(key, when, team, sprint="Sprint 29", points=None):
    rows = [
        [key, f"{when} 09:00:00", "Sprint", None, sprint],
        [key, f"{when} 10:00:00", "labels", None, team],
    ]
    if points is not None:
        rows.append([key, f"{when} 11:00:00", "Story Points", None, str(points)])
    return rows


def scope(events, team="Backend"):
    return scope_changes(events, "Sprint 29", START, REPORT, team, TEAMS, 1)


def facts(**changes):
    return dict(FACTS, **changes)


def test_item_added_after_start_counts_as_added_with_points():
    events = make_events(
        joins("DEMO-1", "2026-03-01", "Backend", points=2)
        + joins("DEMO-2", "2026-03-04", "Backend", points=3)
    )
    assert scope(events)["added"] == {"count": 1, "points": 3}


def test_item_added_on_start_day_is_committed_not_added():
    events = make_events(joins("DEMO-1", "2026-03-02", "Backend", points=2))
    assert scope(events)["added"]["count"] == 0


def test_blank_points_on_added_item_count_as_default():
    events = make_events(joins("DEMO-1", "2026-03-04", "Backend"))
    assert scope(events)["added"] == {"count": 1, "points": 1}


def test_additions_for_another_team_are_excluded():
    events = make_events(joins("DEMO-1", "2026-03-04", "Frontend", points=5))
    assert scope(events)["added"]["count"] == 0


def test_item_removed_after_start_counts_as_removed_at_start_points():
    events = make_events(
        joins("DEMO-1", "2026-03-01", "Backend", points=2)
        + [["DEMO-1", "2026-03-04 09:00:00", "Sprint", "Sprint 29", None]]
    )
    result = scope(events)
    assert result["removed"] == {"count": 1, "points": 2}
    assert result["added"]["count"] == 0


def test_team_facts_counts_block_during_sprint_not_before():
    events = make_events(
        joins("DEMO-1", "2026-03-01", "Backend", points=1)
        + [["DEMO-1", "2026-03-03 09:00:00", "status", "In Progress", "Blocked"]]
        + joins("DEMO-2", "2026-02-26", "Backend", points=1)
        + [["DEMO-2", "2026-02-27 09:00:00", "status", "In Progress", "Blocked"]]
    )
    result = team_facts(events, "Sprint 29", START, REPORT, "Backend", TEAMS, DONE, BLOCKED, 1)
    assert result["blocked_items"] == 1


def test_no_prompts_when_team_is_on_track_too_early_or_not_assessed():
    busy = facts(blank_items=3, open_items=4, open_developers=2, blocked_items=1)
    changed = {"added": {"count": 2, "points": 4}, "removed": {"count": 1, "points": 2}}
    for status in ["On track", "Too early", "Not assessed"]:
        assert where_to_look(status, busy, changed) == []


def test_estimation_prompt_names_added_points_and_blank_items():
    changed = {"added": {"count": 1, "points": 3}, "removed": {"count": 0, "points": 0}}
    prompts = where_to_look("At risk", facts(blank_items=2), changed)
    estimation = [p for p in prompts if p["area"] == "Estimation"]
    assert "3 points were added" in estimation[0]["text"]
    assert "2 of 10" in estimation[0]["text"]


def test_resourcing_prompt_gives_team_figure_per_developer():
    prompts = where_to_look("Off track", facts(open_items=6, open_developers=3), NO_SCOPE)
    resourcing = [p for p in prompts if p["area"] == "Resourcing"]
    assert "about 2.0 each" in resourcing[0]["text"]


def test_unassigned_open_items_are_named_not_hidden():
    prompts = where_to_look("Off track", facts(open_items=6, open_developers=0), NO_SCOPE)
    resourcing = [p for p in prompts if p["area"] == "Resourcing"]
    assert "6 open items have no assignee" in resourcing[0]["text"]


def test_technical_prompt_when_committed_items_were_blocked():
    prompts = where_to_look("At risk", facts(blocked_items=3), NO_SCOPE)
    technical = [p for p in prompts if p["area"] == "Technical or dependency"]
    assert "3 of 10 committed items" in technical[0]["text"]


def test_report_gives_prompts_only_to_at_risk_and_off_track_teams():
    config = load_config()
    report = build_report(
        build_scenario_events(), SCENARIO_SPRINT, SCENARIO_START, SCENARIO_END, REPORT,
        TEAMS, statuses_mapped_to(config, "Done"), statuses_mapped_to(config, "Blocked"),
        holidays_from_csv(holiday_path(config)), status_settings(config),
    )
    by_team = {row["team"]: row for row in report["teams"]}
    assert by_team["Backend"]["status"] == "On track"
    assert by_team["Backend"]["prompts"] == []
    assert by_team["Frontend"]["status"] == "At risk"
    assert by_team["Frontend"]["prompts"]