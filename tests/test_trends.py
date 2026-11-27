from datetime import date

import pandas as pd
import pytest

from dashboard.trends import parse_sprint_lines, trend_for_team

STARTED = {"In Progress"}
DONE = {"Done"}
TEAMS = ["Backend", "Frontend", "DevOps", "QA"]
SETTINGS = {
    "midpoint_working_day": 5,
    "at_risk": 0.05,
    "off_track": 0.10,
    "max_defaulted_share": 0.20,
    "default_points": 1,
}
S1 = ("Sprint 1", date(2026, 3, 2), date(2026, 3, 13))
S2 = ("Sprint 2", date(2026, 3, 16), date(2026, 3, 27))
S3 = ("Sprint 3", date(2026, 3, 30), date(2026, 4, 10))
COLUMNS = ["key", "created", "field", "fromString", "toString"]
HOLIDAYS = set()


def make_events(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def item(key, team, sprint, joined, points="1", started=None, done=None):
    """Events for one item: joins the sprint and team on `joined`, with optional
    points (None for blank), and optional start and Done dates."""
    rows = [
        [key, f"{joined} 09:00:00", "Sprint", None, sprint],
        [key, f"{joined} 10:00:00", "labels", None, team],
    ]
    if points is not None:
        rows.append([key, f"{joined} 11:00:00", "Story Points", None, points])
    if started:
        rows.append([key, f"{started} 09:00:00", "status", "To Do", "In Progress"])
    if done:
        rows.append([key, f"{done} 09:00:00", "status", "In Progress", "Done"])
    return rows



def trend(events, sprints, team="Backend"):
    return trend_for_team(events, sprints, team, TEAMS, STARTED, DONE, SETTINGS, HOLIDAYS)


def test_throughput_counts_committed_items_done_by_sprint_end():
    events = make_events(
        item("A-1", "Backend", "Sprint 1", "2026-03-01", started="2026-03-03", done="2026-03-05")
        + item("A-2", "Backend", "Sprint 1", "2026-03-01", started="2026-03-03", done="2026-03-20")
    )
    assert trend(events, [S1])[0]["throughput"] == 1


def test_items_committed_to_another_team_are_not_counted():
    events = make_events(
        item("A-1", "Frontend", "Sprint 1", "2026-03-01", started="2026-03-03", done="2026-03-05")
    )
    assert trend(events, [S1], team="Backend")[0]["throughput"] == 0


def test_velocity_sums_points_of_done_items():
    events = make_events(
        item("A-1", "Backend", "Sprint 1", "2026-03-01", points="3", started="2026-03-03", done="2026-03-05")
        + item("A-2", "Backend", "Sprint 1", "2026-03-01", points="5", started="2026-03-03", done="2026-03-06")
        + item("A-3", "Backend", "Sprint 1", "2026-03-01", points="2", started="2026-03-03")
    )
    row = trend(events, [S1])[0]
    assert row["speed"] == "velocity"
    assert row["velocity"] == 8


def test_blank_share_over_limit_shows_throughput_not_velocity():
    # 3 of 5 items blank = 60%, over the 20% limit; two items are Done
    events = make_events(
        item("A-1", "Backend", "Sprint 1", "2026-03-01", points=None, started="2026-03-03", done="2026-03-05")
        + item("A-2", "Backend", "Sprint 1", "2026-03-01", points=None, started="2026-03-03")
        + item("A-3", "Backend", "Sprint 1", "2026-03-01", points=None, started="2026-03-03")
        + item("A-4", "Backend", "Sprint 1", "2026-03-01", points="2", started="2026-03-03", done="2026-03-06")
        + item("A-5", "Backend", "Sprint 1", "2026-03-01", points="2", started="2026-03-03")
    )
    row = trend(events, [S1])[0]
    assert row["speed"] == "throughput"
    assert row["velocity"] is None
    assert row["throughput"] == 2


def test_cycle_median_uses_committed_done_items_of_the_team_only():
    events = make_events(
        item("A-1", "Backend", "Sprint 1", "2026-03-01", started="2026-03-03", done="2026-03-05")  # 2 days
        + item("A-2", "Backend", "Sprint 1", "2026-03-01", started="2026-03-03", done="2026-03-09")  # 6 days
        + item("A-3", "Backend", "Sprint 1", "2026-03-01", started="2026-03-03", done="2026-03-11")  # 8 days
        + item("B-1", "Frontend", "Sprint 1", "2026-03-01", started="2026-03-03", done="2026-03-04")  # other team
    )
    assert trend(events, [S1])[0]["cycle_median"] == 6.0


def test_cycle_median_is_none_when_nothing_is_done():
    events = make_events(
        item("A-1", "Backend", "Sprint 1", "2026-03-01", started="2026-03-03")
    )
    assert trend(events, [S1])[0]["cycle_median"] is None


def test_sprint_with_no_committed_items_is_na_with_zero_throughput():
    events = make_events(
        item("A-1", "Frontend", "Sprint 1", "2026-03-01", started="2026-03-03", done="2026-03-05")
    )
    row = trend(events, [S1], team="Backend")[0]
    assert row["speed"] == "N/A"
    assert row["throughput"] == 0
    assert row["velocity"] is None


def test_rolling_velocity_is_blank_until_three_sprints():
    events = make_events(
        item("A-1", "Backend", "Sprint 1", "2026-03-01", points="3", started="2026-03-03", done="2026-03-05")
        + item("B-1", "Backend", "Sprint 2", "2026-03-15", points="4", started="2026-03-17", done="2026-03-19")
    )
    rows = trend(events, [S1, S2])
    assert [row["velocity"] for row in rows] == [3, 4]
    assert [row["rolling_velocity"] for row in rows] == [None, None]


def test_rolling_velocity_averages_the_last_three_sprints():
    events = make_events(
        item("A-1", "Backend", "Sprint 1", "2026-03-01", points="6", started="2026-03-03", done="2026-03-05")
        + item("B-1", "Backend", "Sprint 2", "2026-03-15", points="9", started="2026-03-17", done="2026-03-19")
        + item("C-1", "Backend", "Sprint 3", "2026-03-29", points="12", started="2026-03-31", done="2026-04-08")
    )
    rows = trend(events, [S1, S2, S3])
    assert [row["rolling_velocity"] for row in rows] == [None, None, 9.0]


def test_rolling_velocity_is_blank_when_a_sprint_in_the_window_is_not_assessed():
    # Sprint 2 has only blank points, so its velocity is blank and the window is blank
    events = make_events(
        item("A-1", "Backend", "Sprint 1", "2026-03-01", points="6", started="2026-03-03", done="2026-03-05")
        + item("B-1", "Backend", "Sprint 2", "2026-03-15", points=None, started="2026-03-17", done="2026-03-19")
        + item("B-2", "Backend", "Sprint 2", "2026-03-15", points=None, started="2026-03-17")
        + item("C-1", "Backend", "Sprint 3", "2026-03-29", points="12", started="2026-03-31", done="2026-04-08")
    )
    rows = trend(events, [S1, S2, S3])
    assert rows[1]["velocity"] is None
    assert rows[2]["rolling_velocity"] is None


def test_rows_follow_the_order_of_the_sprints_given():
    events = make_events(
        item("A-1", "Backend", "Sprint 1", "2026-03-01", started="2026-03-03")
    )
    rows = trend(events, [S1, S2])
    assert [row["sprint"] for row in rows] == ["Sprint 1", "Sprint 2"]


def test_parses_name_and_dates():
    assert parse_sprint_lines("Sprint 1, 2026-03-02, 2026-03-13") == [
        ("Sprint 1", date(2026, 3, 2), date(2026, 3, 13))
    ]


def test_name_with_commas_is_kept_whole():
    sprints = parse_sprint_lines("Sprint 5, carry-over, 2026-03-02, 2026-03-13")
    assert sprints[0][0] == "Sprint 5, carry-over"


def test_blank_lines_are_skipped():
    assert len(parse_sprint_lines("\nSprint 1, 2026-03-02, 2026-03-13\n\n")) == 1


def test_bad_line_names_its_line_number():
    with pytest.raises(ValueError, match="Line 2"):
        parse_sprint_lines("Sprint 1, 2026-03-02, 2026-03-13\nSprint 2, 2026-13-99, 2026-03-27")

def test_trend_zero_point_sprint_matches_status_table():
    events = make_events([
        ["A-1", "2026-03-01 09:00:00", "Sprint", None, "Sprint 1"],
        ["A-1", "2026-03-01 10:00:00", "labels", None, "Backend"],
        ["A-1", "2026-03-01 11:00:00", "Story Points", None, "0"],
        ["A-1", "2026-03-02 12:00:00", "status", "To Do", "In Progress"],
        ["A-1", "2026-03-04 09:00:00", "status", "In Progress", "Done"],
    ])
    row = trend(events, [S1])[0]
    assert row["status"] == "Not assessed"
    assert row["speed"] == "throughput"
    assert row["throughput"] == 1
    assert row["velocity"] is None


def test_trend_cycle_time_counts_calendar_days_between_dates():
    events = make_events([
        ["A-1", "2026-03-01 09:00:00", "Sprint", None, "Sprint 1"],
        ["A-1", "2026-03-01 10:00:00", "labels", None, "Backend"],
        ["A-1", "2026-03-01 11:00:00", "Story Points", None, "1"],
        ["A-1", "2026-03-02 12:00:00", "status", "To Do", "In Progress"],
        ["A-1", "2026-03-04 09:00:00", "status", "In Progress", "Done"],
    ])
    assert trend(events, [S1])[0]["cycle_median"] == 2.0