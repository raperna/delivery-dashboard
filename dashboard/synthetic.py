from datetime import date

import pandas as pd

SPRINT = "Sprint 29"
START = date(2026, 3, 2)
END = date(2026, 3, 13)
TEAMS = ["Backend", "Frontend", "DevOps", "QA"]
DONE = {"Done"}
BLOCKED = {"Blocked"}
COLUMNS = ["key", "created", "field", "fromString", "toString"]

# Hand-worked answers: sprint is 10 working days, report on Fri 6 March is day 5.
EXPECTED_STATUS = {
    ("Backend", date(2026, 3, 4)): "Too early",   # day 3, before the midpoint
    ("Backend", date(2026, 3, 6)): "On track",    # expected 2, done 2
    ("Frontend", date(2026, 3, 6)): "At risk",    # expected 20, done 18: shortfall 5%
    ("DevOps", date(2026, 3, 6)): "Off track",    # expected 5, done 0: shortfall 100%
    ("QA", date(2026, 3, 6)): "Not assessed",     # 6 of 10 items blank: 60% over the limit
}

# One blocker with no team label, blocked on Tue 3 March, reported on Fri 6 March.
EXPECTED_BLOCKED = [("DEMO-BLK-1", "Team Unassigned", 3)]


def _team_rows(prefix, team, points, done_count, done_when):
    """One row per event. `points` has one entry per item; None means blank."""
    rows = []
    for index, value in enumerate(points, start=1):
        key = f"{prefix}-{index}"
        rows.append([key, "2026-03-01 09:00:00", "Sprint", None, SPRINT])
        rows.append([key, "2026-03-01 10:00:00", "labels", None, team])
        if value is not None:
            rows.append([key, "2026-03-01 11:00:00", "Story Points", None, str(value)])
        rows.append([key, "2026-03-02 12:00:00", "status", "To Do", "In Progress"])
        if index <= done_count:
            rows.append([key, done_when, "status", "In Progress", "Done"])
    return rows


def _blocked_rows():
    key = "DEMO-BLK-1"
    return [
        [key, "2026-03-02 09:00:00", "status", "To Do", "In Progress"],
        [key, "2026-03-03 09:00:00", "status", "In Progress", "Blocked"],
    ]


def build_scenario_events():
    """Changelog rows for the four teams and one blocker, as a DataFrame."""
    done_when = "2026-03-04 09:00:00"
    rows = []
    rows += _team_rows("BE", "Backend", [1] * 4, 2, done_when)
    rows += _team_rows("FE", "Frontend", [1] * 40, 18, done_when)
    rows += _team_rows("DO", "DevOps", [1] * 10, 0, done_when)
    rows += _team_rows("QA", "QA", [None] * 6 + [3, 3, 3, 3], 0, done_when)
    rows += _blocked_rows()
    return pd.DataFrame(rows, columns=COLUMNS)

def build_scale_events(items_per_team, done_per_team):
    """Large changelog for the scale check: four teams in one sprint (D-038).

    done_per_team maps each team to how many of its items are Done on 4 March.
    Every item has 1 point, so the expected numbers can be worked out by hand.
    """
    rows = []
    for team in TEAMS:
        prefix = team[:2].upper()
        done_count = done_per_team[team]
        for index in range(1, items_per_team + 1):
            key = f"{prefix}-{index}"
            rows.append([key, "2026-03-01 09:00:00", "Sprint", None, SPRINT])
            rows.append([key, "2026-03-01 10:00:00", "labels", None, team])
            rows.append([key, "2026-03-01 11:00:00", "Story Points", None, "1"])
            rows.append([key, "2026-03-02 12:00:00", "status", "To Do", "In Progress"])
            if index <= done_count:
                rows.append([key, "2026-03-04 09:00:00", "status", "In Progress", "Done"])
    return pd.DataFrame(rows, columns=COLUMNS)