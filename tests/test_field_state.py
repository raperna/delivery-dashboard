from datetime import datetime

import pandas as pd

from dashboard.events import field_state, points_state, value_on


def make_events(rows):
    return pd.DataFrame(
        rows, columns=["key", "created", "field", "fromString", "toString"]
    )


def test_latest_value_at_cutoff_wins():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "status", "To Do", "In Progress"],
        ["DEMO-1", "2024-03-07 09:00:00", "status", "In Progress", "Done"],
    ])
    state = field_state(events, "status", datetime(2024, 3, 6))
    assert value_on(state, "DEMO-1") == "In Progress"


def test_value_before_first_event_is_none():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "status", "To Do", "In Progress"],
    ])
    state = field_state(events, "status", datetime(2024, 3, 3))
    assert value_on(state, "DEMO-1") is None


def test_cleared_value_is_none_not_zero():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Story Points", None, "5"],
        ["DEMO-1", "2024-03-06 09:00:00", "Story Points", "5", None],
    ])
    state = points_state(events, datetime(2024, 3, 7))
    assert value_on(state, "DEMO-1") is None


def test_events_after_cutoff_are_ignored():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "status", "To Do", "In Progress"],
        ["DEMO-1", "2024-03-09 09:00:00", "status", "In Progress", "Done"],
    ])
    state = field_state(events, "status", datetime(2024, 3, 6))
    assert value_on(state, "DEMO-1") == "In Progress"


def test_other_fields_do_not_change_the_value():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "status", "To Do", "In Progress"],
        ["DEMO-1", "2024-03-05 09:00:00", "labels", None, "Backend"],
    ])
    state = field_state(events, "status", datetime(2024, 3, 6))
    assert value_on(state, "DEMO-1") == "In Progress"


def test_points_are_read_as_numbers():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Story Points", None, "5"],
        ["DEMO-2", "2024-03-04 09:00:00", "Story Points", None, "0"],
    ])
    state = points_state(events, datetime(2024, 3, 5))
    assert value_on(state, "DEMO-1") == 5.0
    assert value_on(state, "DEMO-2") == 0.0


def test_numeric_cell_values_are_kept_not_treated_as_blank():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Story Points", None, 3],
    ])
    state = points_state(events, datetime(2024, 3, 5))
    assert value_on(state, "DEMO-1") == 3.0