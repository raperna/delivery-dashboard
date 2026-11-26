from datetime import datetime

import pandas as pd

from dashboard.events import sprint_state, sprints_on


def make_events(rows):
    return pd.DataFrame(
        rows, columns=["key", "created", "field", "fromString", "toString"]
    )


def test_sprint_is_present_after_it_was_added():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Sprint", None, "Sprint 29"],
    ])
    state = sprint_state(events, as_of=datetime(2024, 3, 5))
    assert sprints_on(state, "DEMO-1") == {"Sprint 29"}


def test_sprint_is_absent_before_it_was_added():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Sprint", None, "Sprint 29"],
    ])
    state = sprint_state(events, as_of=datetime(2024, 3, 3))
    assert sprints_on(state, "DEMO-1") == set()


def test_full_list_replaces_previous_state_not_merged():
    # Sprint events hold the full list, so Sprint 29 leaves when it's absent
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Sprint", None, "Sprint 29"],
        ["DEMO-1", "2024-03-06 09:00:00", "Sprint", "Sprint 29", "Sprint 30"],
    ])
    state = sprint_state(events, as_of=datetime(2024, 3, 7))
    assert sprints_on(state, "DEMO-1") == {"Sprint 30"}


def test_removal_takes_effect_on_its_date():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Sprint", None, "Sprint 29, Sprint 30"],
        ["DEMO-1", "2024-03-06 09:00:00", "Sprint", "Sprint 29, Sprint 30", "Sprint 29"],
    ])
    assert sprints_on(sprint_state(events, datetime(2024, 3, 5)), "DEMO-1") == {"Sprint 29", "Sprint 30"}
    assert sprints_on(sprint_state(events, datetime(2024, 3, 7)), "DEMO-1") == {"Sprint 29"}


def test_removed_then_re_added_is_present_only_after_re_add():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Sprint", None, "Sprint 29"],
        ["DEMO-1", "2024-03-06 09:00:00", "Sprint", "Sprint 29", None],
        ["DEMO-1", "2024-03-09 09:00:00", "Sprint", None, "Sprint 29"],
    ])
    assert sprints_on(sprint_state(events, datetime(2024, 3, 7)), "DEMO-1") == set()
    assert sprints_on(sprint_state(events, datetime(2024, 3, 10)), "DEMO-1") == {"Sprint 29"}


def test_events_after_the_as_of_date_are_ignored():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Sprint", None, "Sprint 29"],
        ["DEMO-1", "2024-03-08 09:00:00", "Sprint", "Sprint 29", "Sprint 30"],
    ])
    state = sprint_state(events, as_of=datetime(2024, 3, 6))
    assert sprints_on(state, "DEMO-1") == {"Sprint 29"}


def test_events_for_other_fields_do_not_change_sprints():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Sprint", None, "Sprint 29"],
        ["DEMO-1", "2024-03-05 09:00:00", "labels", None, "Backend"],
    ])
    state = sprint_state(events, as_of=datetime(2024, 3, 6))
    assert sprints_on(state, "DEMO-1") == {"Sprint 29"}


def test_issue_with_no_events_has_no_sprints():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Sprint", None, "Sprint 29"],
    ])
    state = sprint_state(events, as_of=datetime(2024, 3, 5))
    assert sprints_on(state, "DEMO-99") == set()


def test_sprint_names_with_spaces_and_digits_are_kept_whole():
    events = make_events([
        ["DEMO-1", "2024-03-04 09:00:00", "Sprint", None, "Twitter Aurora Q4 Sprint 5"],
    ])
    state = sprint_state(events, as_of=datetime(2024, 3, 5))
    assert sprints_on(state, "DEMO-1") == {"Twitter Aurora Q4 Sprint 5"}