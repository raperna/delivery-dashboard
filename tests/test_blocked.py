from datetime import date

import pandas as pd

from dashboard.blocked import blocked_items

TEAMS = ["Backend", "Frontend", "DevOps", "QA"]
BLOCKED = {"Blocked"}
REPORT = date(2026, 3, 10)
HOLIDAYS = set()


def make_events(rows):
    return pd.DataFrame(
        rows, columns=["key", "created", "field", "fromString", "toString"]
    )


def block(key, when):
    return [key, when, "status", "In Progress", "Blocked"]


def unblock(key, when):
    return [key, when, "status", "Blocked", "In Progress"]


def label(key, when, name):
    return [key, when, "labels", None, name]


def assignee(key, when, name):
    return [key, when, "assignee", None, name]


def run(events, report_date=REPORT):
    return blocked_items(events, report_date, BLOCKED, TEAMS, HOLIDAYS)


def keys(rows):
    return [row["key"] for row in rows]


def test_currently_blocked_item_is_listed():
    events = make_events([block("DEMO-1", "2026-03-05 09:00:00")])
    assert keys(run(events)) == ["DEMO-1"]


def test_item_unblocked_before_report_date_is_excluded():
    events = make_events([
        block("DEMO-1", "2026-03-05 09:00:00"),
        unblock("DEMO-1", "2026-03-07 09:00:00"),
    ])
    assert keys(run(events)) == []


def test_item_blocked_after_report_date_is_excluded():
    events = make_events([block("DEMO-1", "2026-03-11 09:00:00")])
    assert keys(run(events)) == []


def test_days_waiting_counts_working_days_after_the_block():
    # Blocked Thu 5 March; working days after it up to Mon 9 March: Fri 6, Mon 9
    events = make_events([block("DEMO-1", "2026-03-05 09:00:00")])
    assert run(events, report_date=date(2026, 3, 9))[0]["days_waiting"] == 2


def test_weekend_does_not_add_days_waiting():
    # Blocked Fri 6 March; on Mon 9 March only one working day has passed
    events = make_events([block("DEMO-1", "2026-03-06 09:00:00")])
    assert run(events, report_date=date(2026, 3, 9))[0]["days_waiting"] == 1


def test_same_day_block_has_zero_days_waiting():
    events = make_events([block("DEMO-1", "2026-03-06 09:00:00")])
    assert run(events, report_date=date(2026, 3, 6))[0]["days_waiting"] == 0


def test_holiday_is_not_counted_as_waiting():
    # Blocked Fri 22 May; Mon 25 May is a holiday; on Tue 26 May one working day has passed
    events = make_events([block("DEMO-1", "2026-05-22 09:00:00")])
    rows = blocked_items(events, date(2026, 5, 26), BLOCKED, TEAMS, {date(2026, 5, 25)})
    assert rows[0]["days_waiting"] == 1


def test_reblocked_item_waits_from_its_latest_block():
    events = make_events([
        block("DEMO-1", "2026-03-02 09:00:00"),
        unblock("DEMO-1", "2026-03-04 09:00:00"),
        block("DEMO-1", "2026-03-08 09:00:00"),
    ])
    assert run(events)[0]["days_waiting"] == 2


def test_sorted_longest_wait_first():
    events = make_events([
        block("DEMO-1", "2026-03-08 09:00:00"),
        block("DEMO-2", "2026-03-03 09:00:00"),
    ])
    assert keys(run(events)) == ["DEMO-2", "DEMO-1"]


def test_non_blocked_items_are_ignored():
    events = make_events([
        block("DEMO-1", "2026-03-05 09:00:00"),
        ["DEMO-2", "2026-03-05 09:00:00", "status", "In Progress", "Done"],
    ])
    assert keys(run(events)) == ["DEMO-1"]


def test_team_comes_from_label_on_report_date():
    events = make_events([
        block("DEMO-1", "2026-03-05 09:00:00"),
        label("DEMO-1", "2026-03-01 10:00:00", "Backend"),
    ])
    row = run(events)[0]
    assert row["team"] == "Backend"
    assert row["team_flag"] == "ok"


def test_label_added_after_report_date_is_not_used():
    events = make_events([
        block("DEMO-1", "2026-03-05 09:00:00"),
        label("DEMO-1", "2026-03-11 10:00:00", "Backend"),
    ])
    row = run(events)[0]
    assert row["team"] == "Team Unassigned"


def test_no_team_label_is_team_unassigned_and_flagged():
    events = make_events([block("DEMO-1", "2026-03-05 09:00:00")])
    row = run(events)[0]
    assert row["team"] == "Team Unassigned"
    assert row["team_flag"] == "no_team"


def test_two_team_labels_are_team_unassigned_conflict():
    events = make_events([
        block("DEMO-1", "2026-03-05 09:00:00"),
        label("DEMO-1", "2026-03-01 10:00:00", "Backend"),
        label("DEMO-1", "2026-03-01 11:00:00", "QA"),
    ])
    row = run(events)[0]
    assert row["team"] == "Team Unassigned"
    assert row["team_flag"] == "conflict"


def test_team_match_is_case_insensitive():
    events = make_events([
        block("DEMO-1", "2026-03-05 09:00:00"),
        label("DEMO-1", "2026-03-01 10:00:00", "backend"),
    ])
    assert run(events)[0]["team"] == "Backend"


def test_developer_is_assignee_on_report_date():
    events = make_events([
        block("DEMO-1", "2026-03-05 09:00:00"),
        assignee("DEMO-1", "2026-03-06 09:00:00", "alice"),
    ])
    assert run(events)[0]["developer"] == "alice"


def test_reassignment_after_report_date_shows_earlier_assignee():
    events = make_events([
        block("DEMO-1", "2026-03-05 09:00:00"),
        assignee("DEMO-1", "2026-03-06 09:00:00", "alice"),
        assignee("DEMO-1", "2026-03-11 09:00:00", "bob"),
    ])
    assert run(events)[0]["developer"] == "alice"


def test_unassigned_item_has_no_developer():
    events = make_events([block("DEMO-1", "2026-03-05 09:00:00")])
    assert run(events)[0]["developer"] is None