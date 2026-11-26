from datetime import date

import pandas as pd

from dashboard.commitment import commitment_at_start

TEAMS = ["Backend", "Frontend", "DevOps", "QA"]
START = date(2024, 3, 4)


def make_events(rows):
    return pd.DataFrame(
        rows, columns=["key", "created", "field", "fromString", "toString"]
    )


def test_item_in_sprint_at_start_is_committed():
    events = make_events([
        ["DEMO-1", "2024-03-03 10:00:00", "Sprint", None, "Sprint 29"],
    ])
    result = commitment_at_start(events, "Sprint 29", START, TEAMS)
    assert list(result["key"]) == ["DEMO-1"]


def test_item_added_after_start_day_is_not_committed():
    events = make_events([
        ["DEMO-1", "2024-03-05 10:00:00", "Sprint", None, "Sprint 29"],
    ])
    result = commitment_at_start(events, "Sprint 29", START, TEAMS)
    assert list(result["key"]) == []


def test_item_added_on_start_day_counts_as_committed():
    events = make_events([
        ["DEMO-1", "2024-03-04 16:00:00", "Sprint", None, "Sprint 29"],
    ])
    result = commitment_at_start(events, "Sprint 29", START, TEAMS)
    assert list(result["key"]) == ["DEMO-1"]


def test_item_removed_mid_sprint_is_still_committed():
    events = make_events([
        ["DEMO-1", "2024-03-03 10:00:00", "Sprint", None, "Sprint 29"],
        ["DEMO-1", "2024-03-06 10:00:00", "Sprint", "Sprint 29", None],
    ])
    result = commitment_at_start(events, "Sprint 29", START, TEAMS)
    assert list(result["key"]) == ["DEMO-1"]


def test_item_in_other_sprint_is_excluded():
    events = make_events([
        ["DEMO-1", "2024-03-03 10:00:00", "Sprint", None, "Sprint 28"],
    ])
    result = commitment_at_start(events, "Sprint 29", START, TEAMS)
    assert list(result["key"]) == []


def test_team_comes_from_label_at_start():
    events = make_events([
        ["DEMO-1", "2024-03-03 10:00:00", "Sprint", None, "Sprint 29"],
        ["DEMO-1", "2024-03-03 11:00:00", "labels", None, "Backend"],
    ])
    result = commitment_at_start(events, "Sprint 29", START, TEAMS)
    row = result.set_index("key").loc["DEMO-1"]
    assert row["team"] == "Backend"
    assert row["team_flag"] == "ok"


def test_label_added_after_start_is_not_used():
    events = make_events([
        ["DEMO-1", "2024-03-03 10:00:00", "Sprint", None, "Sprint 29"],
        ["DEMO-1", "2024-03-06 11:00:00", "labels", None, "Backend"],
    ])
    result = commitment_at_start(events, "Sprint 29", START, TEAMS)
    row = result.set_index("key").loc["DEMO-1"]
    assert row["team"] is None
    assert row["team_flag"] == "no_team"


def test_item_without_team_label_is_flagged():
    events = make_events([
        ["DEMO-1", "2024-03-03 10:00:00", "Sprint", None, "Sprint 29"],
        ["DEMO-1", "2024-03-03 11:00:00", "labels", None, "PatchAvailable"],
    ])
    result = commitment_at_start(events, "Sprint 29", START, TEAMS)
    row = result.set_index("key").loc["DEMO-1"]
    assert row["team"] is None
    assert row["team_flag"] == "no_team"


def test_two_team_labels_are_a_conflict():
    events = make_events([
        ["DEMO-1", "2024-03-03 10:00:00", "Sprint", None, "Sprint 29"],
        ["DEMO-1", "2024-03-03 11:00:00", "labels", None, "Backend"],
        ["DEMO-1", "2024-03-03 11:05:00", "labels", None, "QA"],
    ])
    result = commitment_at_start(events, "Sprint 29", START, TEAMS)
    row = result.set_index("key").loc["DEMO-1"]
    assert row["team"] is None
    assert row["team_flag"] == "conflict"


def test_team_match_is_case_insensitive():
    events = make_events([
        ["DEMO-1", "2024-03-03 10:00:00", "Sprint", None, "Sprint 29"],
        ["DEMO-1", "2024-03-03 11:00:00", "labels", None, "backend"],
    ])
    result = commitment_at_start(events, "Sprint 29", START, TEAMS)
    row = result.set_index("key").loc["DEMO-1"]
    assert row["team"] == "Backend"