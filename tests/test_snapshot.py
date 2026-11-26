from datetime import date

import pandas as pd
from dashboard.snapshot import team_items, team_report

START = date(2026, 3, 2)
END = date(2026, 3, 13)
REPORT = date(2026, 3, 6)
TEAMS = ["Backend", "Frontend", "DevOps", "QA"]
DONE = {"Done"}
HOLIDAYS = set()
SETTINGS = {
    "midpoint_working_day": 5,
    "at_risk": 0.05,
    "off_track": 0.10,
    "max_defaulted_share": 0.20,
    "default_points": 1,
}


def make_events(rows):
    return pd.DataFrame(
        rows, columns=["key", "created", "field", "fromString", "toString"]
    )


def item_rows(key, team="Backend", sprint="Sprint 29", points="1", when="2026-03-01"):
    rows = [[key, f"{when} 09:00:00", "Sprint", None, sprint]]
    if team is not None:
        rows.append([key, f"{when} 10:00:00", "labels", None, team])
    if points is not None:
        rows.append([key, f"{when} 11:00:00", "Story Points", None, points])
    return rows


def done_rows(key, when):
    return [[key, when, "status", "In Progress", "Done"]]


def team_rows(count, points="1", done=0):
    """`count` Backend items in Sprint 29; the first `done` are Done on Wed 4 March."""
    rows = []
    for index in range(1, count + 1):
        key = f"DEMO-{index}"
        rows += item_rows(key, points=points)
        if index <= done:
            rows += done_rows(key, "2026-03-04 09:00:00")
    return make_events(rows)


def items_for(events, team="Backend", report_date=REPORT):
    return team_items(events, "Sprint 29", START, team, TEAMS, DONE, report_date)


def keys(items):
    return [item["key"] for item in items]


def report(events, report_date=REPORT):
    return team_report(
        events, "Sprint 29", START, END, report_date, "Backend", TEAMS, DONE, HOLIDAYS, SETTINGS
    )


def test_lists_only_committed_items_for_the_team():
    events = make_events(item_rows("DEMO-1", team="Backend") + item_rows("DEMO-2", team="Frontend"))
    assert keys(items_for(events)) == ["DEMO-1"]


def test_points_are_taken_from_start_day():
    events = make_events(
        item_rows("DEMO-1", points="3") + [["DEMO-1", "2026-03-04 09:00:00", "Story Points", "3", "5"]]
    )
    assert items_for(events)[0]["points"] == 3.0


def test_item_added_after_start_is_excluded():
    events = make_events([
        ["DEMO-1", "2026-03-01 10:00:00", "labels", None, "Backend"],
        ["DEMO-1", "2026-03-04 10:00:00", "Sprint", None, "Sprint 29"],
    ])
    assert keys(items_for(events)) == []


def test_done_when_status_is_done_on_report_date():
    events = make_events(item_rows("DEMO-1") + done_rows("DEMO-1", "2026-03-05 09:00:00"))
    assert items_for(events)[0]["done"] is True


def test_not_done_when_done_only_after_report_date():
    events = make_events(item_rows("DEMO-1") + done_rows("DEMO-1", "2026-03-09 09:00:00"))
    assert items_for(events)[0]["done"] is False


def test_not_done_when_status_is_still_in_progress():
    events = make_events(
        item_rows("DEMO-1") + [["DEMO-1", "2026-03-03 09:00:00", "status", "To Do", "In Progress"]]
    )
    assert items_for(events)[0]["done"] is False


def test_item_with_no_status_events_is_not_done():
    events = make_events(item_rows("DEMO-1"))
    assert items_for(events)[0]["done"] is False


def test_blank_points_at_start_stay_blank():
    events = make_events(item_rows("DEMO-1", points=None))
    assert items_for(events)[0]["points"] is None


def test_item_with_two_team_labels_is_excluded():
    events = make_events(
        item_rows("DEMO-1", team="Backend") + [["DEMO-1", "2026-03-01 12:00:00", "labels", None, "QA"]]
    )
    assert keys(items_for(events)) == []


def test_team_report_on_track_when_done_matches_expected():
    # 4 items, 1 point each: expected 2 at the midpoint, done 2
    result = report(team_rows(4, done=2))
    assert result["status"] == "On track"


def test_team_report_too_early_before_midpoint():
    # Wednesday 4 March is working day 3
    result = report(team_rows(4), report_date=date(2026, 3, 4))
    assert result["status"] == "Too early"


def test_team_report_not_assessed_when_points_are_blank():
    result = report(team_rows(4, points=None))
    assert result["status"] == "Not assessed"
    assert result["speed"] == "throughput"


def test_team_report_off_track_when_nothing_is_done():
    # 10 items, expected 5 at the midpoint, done 0: shortfall 100%
    result = report(team_rows(10))
    assert result["status"] == "Off track"