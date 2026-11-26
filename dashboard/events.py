import math

import pandas as pd

from dashboard.sprints import split_sprints


def _is_blank(value):
    """A blank cell arrives as None, NaN, or an empty string. A 0 is not blank."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and value == ""


def _events_until(events, field, as_of):
    """Return events for one field created on or before as_of, in time order."""
    selected = events[events["field"] == field].copy()
    selected["created"] = pd.to_datetime(selected["created"])
    selected = selected[selected["created"] <= pd.Timestamp(as_of)]
    return selected.sort_values("created", kind="stable")


def field_state(events, field, as_of):
    """Rebuild a single-valued field for each issue as it was on as_of.

    The latest event at or before as_of wins. A cleared value gives None.
    Returns a dict of issue key -> value, or None.
    """
    state = {}
    for _, row in _events_until(events, field, as_of).iterrows():
        state[row["key"]] = None if _is_blank(row["toString"]) else row["toString"]
    return state


def value_on(state, key):
    """Return one issue's value from a field_state result, or None."""
    return state.get(key)


def points_state(events, as_of):
    """Story points per issue on as_of, as numbers. Blank stays None (D-021)."""
    raw = field_state(events, "Story Points", as_of)
    return {
        key: None if value is None else float(value)
        for key, value in raw.items()
    }


def label_state(events, as_of):
    """Rebuild each issue's labels as they were on as_of.

    A fromString value removes that label; a toString value adds one. A single
    event can do both, as a rename does. Returns a dict of issue key -> set of labels.
    """
    state = {}
    for _, row in _events_until(events, "labels", as_of).iterrows():
        labels = state.setdefault(row["key"], set())
        if not _is_blank(row["fromString"]):
            labels.discard(row["fromString"])
        if not _is_blank(row["toString"]):
            labels.add(row["toString"])
    return state


def labels_on(state, key):
    """Return the set of labels for one issue, or an empty set if it has none."""
    return set(state.get(key, set()))


def sprint_state(events, as_of):
    """Rebuild each issue's sprint membership as it was on as_of.

    Sprint events store the full list after each change, so the latest list wins.
    Returns a dict of issue key -> set of sprint names.
    """
    state = {}
    for _, row in _events_until(events, "Sprint", as_of).iterrows():
        state[row["key"]] = set(split_sprints(row["toString"]))
    return state


def sprints_on(state, key):
    """Return the set of sprints for one issue, or an empty set if it has none."""
    return set(state.get(key, set()))

def last_change_time(events, field, as_of):
    """Timestamp of each issue's latest event for one field, at or before as_of."""
    state = {}
    for _, row in _events_until(events, field, as_of).iterrows():
        state[row["key"]] = row["created"]
    return state

def first_event_time(events, field, values, as_of):
    """Timestamp of each issue's first event for one field whose value is in `values`."""
    state = {}
    for _, row in _events_until(events, field, as_of).iterrows():
        if row["toString"] in values and row["key"] not in state:
            state[row["key"]] = row["created"]
    return state