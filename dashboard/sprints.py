import math

SEPARATOR = ", "


def split_sprints(value):
    """Split a Sprint field value into sprint names.

    Jira stores the full sprint list after each change, joined by comma-space.
    An empty cell arrives from pandas as NaN, and an empty sprint list is "".
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    text = str(value).strip()
    if not text:
        return []
    return text.split(SEPARATOR)


def sprint_changes(values):
    """Turn a sequence of full-list Sprint values into per-event changes.

    Returns one (added, removed) pair of sets for each event. The first event
    is compared with an empty state, so every sprint in it counts as added.
    """
    previous = set()
    changes = []
    for value in values:
        current = set(split_sprints(value))
        changes.append((current - previous, previous - current))
        previous = current
    return changes