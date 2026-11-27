import bisect
import math

import pandas as pd

from dashboard.sprints import split_sprints

# One-slot cache: the prepared rows for the last events table passed in.
# The table is held by reference, so its identity cannot be reused (D-041).
_prepared_cache = {"events": None, "by_field": {}}


def _is_blank(value):
    """A blank cell arrives as None, NaN, or an empty string. A 0 is not blank."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and value == ""


def _prepared(events, field):
    """Rows for one field, sorted by time, prepared once per events table (D-041)."""
    if _prepared_cache["events"] is not events:
        _prepared_cache["events"] = events
        _prepared_cache["by_field"] = {}
    by_field = _prepared_cache["by_field"]
    if field not in by_field:
        selected = events[events["field"] == field]
        created = pd.to_datetime(selected["created"]).tolist()
        rows = list(zip(
            selected["key"].tolist(),
            created,
            selected["fromString"].tolist(),
            selected["toString"].tolist(),
        ))
        order = sorted(range(len(rows)), key=lambda i: created[i])
        by_field[field] = ([created[i] for i in order], [rows[i] for i in order])
    return by_field[field]


def _field_rows(events, field, as_of):
    """Rows for one field created on or before as_of, in time order.

    Each row is (key, created, from, to). The cutoff is found by binary search.
    """
    times, rows = _prepared(events, field)
    end = bisect.bisect_right(times, pd.Timestamp(as_of))
    return rows[:end]


def field_state(events, field, as_of):
    """Rebuild a single-valued field for each issue as it was on as_of.

    The latest event at or before as_of wins. A cleared value gives None.
    Returns a dict of issue key -> value, or None.
    """
    state = {}
    for key, _, _, to in _field_rows(events, field, as_of):
        state[key] = None if _is_blank(to) else to
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
    for key, _, removed, added in _field_rows(events, "labels", as_of):
        labels = state.setdefault(key, set())
        if not _is_blank(removed):
            labels.discard(removed)
        if not _is_blank(added):
            labels.add(added)
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
    for key, _, _, to in _field_rows(events, "Sprint", as_of):
        state[key] = set(split_sprints(to))
    return state


def sprints_on(state, key):
    """Return the set of sprints for one issue, or an empty set if it has none."""
    return set(state.get(key, set()))


def first_event_time(events, field, values, as_of):
    """Timestamp of each issue's first event for one field whose value is in `values`."""
    state = {}
    for key, created, _, to in _field_rows(events, field, as_of):
        if to in values and key not in state:
            state[key] = created
    return state


def last_change_time(events, field, as_of):
    """Timestamp of each issue's latest event for one field, at or before as_of."""
    state = {}
    for key, created, _, _ in _field_rows(events, field, as_of):
        state[key] = created
    return state