from datetime import datetime

import pandas as pd

from dashboard.events import label_state, labels_on


def make_events(rows):
    return pd.DataFrame(
        rows, columns=["key", "created", "field", "fromString", "toString"]
    )


def test_label_is_present_after_it_was_added():
    events = make_events([
        ["DEMO-1", "2024-03-05 11:00:00", "labels", None, "Backend"],
    ])
    state = label_state(events, as_of=datetime(2024, 3, 6))
    assert labels_on(state, "DEMO-1") == {"Backend"}


def test_label_is_absent_before_it_was_added():
    events = make_events([
        ["DEMO-1", "2024-03-05 11:00:00", "labels", None, "Backend"],
    ])
    state = label_state(events, as_of=datetime(2024, 3, 4))
    assert labels_on(state, "DEMO-1") == set()


def test_event_on_the_as_of_moment_is_included():
    events = make_events([
        ["DEMO-1", "2024-03-06 09:00:00", "labels", None, "Backend"],
    ])
    state = label_state(events, as_of=datetime(2024, 3, 6, 9, 0))
    assert labels_on(state, "DEMO-1") == {"Backend"}


def test_removal_takes_effect_on_its_date():
    events = make_events([
        ["DEMO-1", "2024-03-05 11:00:00", "labels", None, "Backend"],
        ["DEMO-1", "2024-03-07 10:00:00", "labels", "Backend", None],
    ])
    assert labels_on(label_state(events, datetime(2024, 3, 6)), "DEMO-1") == {"Backend"}
    assert labels_on(label_state(events, datetime(2024, 3, 8)), "DEMO-1") == set()


def test_label_removed_then_added_again_is_present_only_after_re_add():
    events = make_events([
        ["DEMO-1", "2024-03-05 11:00:00", "labels", None, "Backend"],
        ["DEMO-1", "2024-03-07 10:00:00", "labels", "Backend", None],
        ["DEMO-1", "2024-03-10 09:00:00", "labels", None, "Backend"],
    ])
    assert labels_on(label_state(events, datetime(2024, 3, 8)), "DEMO-1") == set()
    assert labels_on(label_state(events, datetime(2024, 3, 11)), "DEMO-1") == {"Backend"}


def test_rename_in_one_event_removes_old_label_and_adds_new():
    events = make_events([
        ["DEMO-1", "2024-03-05 11:00:00", "labels", None, "Backend"],
        ["DEMO-1", "2024-03-07 10:00:00", "labels", "Backend", "Frontend"],
    ])
    state = label_state(events, as_of=datetime(2024, 3, 8))
    assert labels_on(state, "DEMO-1") == {"Frontend"}


def test_events_after_the_as_of_date_are_ignored():
    events = make_events([
        ["DEMO-1", "2024-03-05 11:00:00", "labels", None, "Backend"],
        ["DEMO-1", "2024-03-09 11:00:00", "labels", None, "QA"],
    ])
    state = label_state(events, as_of=datetime(2024, 3, 6))
    assert labels_on(state, "DEMO-1") == {"Backend"}


def test_labels_are_tracked_separately_per_label():
    events = make_events([
        ["DEMO-1", "2024-03-05 11:00:00", "labels", None, "Backend"],
        ["DEMO-1", "2024-03-06 11:00:00", "labels", None, "QA"],
        ["DEMO-1", "2024-03-07 10:00:00", "labels", "Backend", None],
    ])
    state = label_state(events, as_of=datetime(2024, 3, 8))
    assert labels_on(state, "DEMO-1") == {"QA"}


def test_events_for_other_fields_do_not_change_labels():
    events = make_events([
        ["DEMO-1", "2024-03-05 11:00:00", "labels", None, "Backend"],
        ["DEMO-1", "2024-03-06 11:00:00", "status", "To Do", "In Progress"],
    ])
    state = label_state(events, as_of=datetime(2024, 3, 7))
    assert labels_on(state, "DEMO-1") == {"Backend"}


def test_issue_with_no_events_has_no_labels():
    events = make_events([
        ["DEMO-1", "2024-03-05 11:00:00", "labels", None, "Backend"],
    ])
    state = label_state(events, as_of=datetime(2024, 3, 6))
    assert labels_on(state, "DEMO-99") == set()