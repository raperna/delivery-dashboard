import pandas as pd


def label_state(events, as_of):
    """Rebuild each issue's labels as they were on `as_of`.

    Replays only the label events created on or before `as_of`, in time order.
    A fromString value removes that label; a toString value adds one. A single
    event can do both, as a rename does. Returns a dict of issue key -> set of labels.
    """
    label_events = events[events["field"] == "labels"].copy()
    label_events["created"] = pd.to_datetime(label_events["created"])
    label_events = label_events[label_events["created"] <= pd.Timestamp(as_of)]
    label_events = label_events.sort_values("created", kind="stable")

    state = {}
    for _, row in label_events.iterrows():
        labels = state.setdefault(row["key"], set())
        removed = row["fromString"]
        added = row["toString"]
        if isinstance(removed, str):
            labels.discard(removed)
        if isinstance(added, str):
            labels.add(added)
    return state


def labels_on(state, key):
    """Return the set of labels for one issue, or an empty set if it has none."""
    return set(state.get(key, set()))