from datetime import datetime, time

import pandas as pd

from dashboard.events import label_state, labels_on, sprint_state


def _end_of_day(day):
    return datetime.combine(day, time(23, 59, 59))


def commitment_at_start(events, sprint_name, start_date, team_labels):
    """List the items committed to one sprint, with their team as of its start (D-020).

    An item is committed if it is in the sprint at the end of the start day.
    Its team is the single configured team label it has at that moment.
    Items with no team label, or more than one, get team=None and a flag.
    Label matching ignores case, and the configured spelling is returned.
    """
    as_of = _end_of_day(start_date)
    sprints = sprint_state(events, as_of)
    labels = label_state(events, as_of)
    team_lookup = {name.lower(): name for name in team_labels}

    rows = []
    for key, members in sprints.items():
        if sprint_name not in members:
            continue
        found = {
            team_lookup[label.lower()]
            for label in labels_on(labels, key)
            if label.lower() in team_lookup
        }
        if len(found) == 0:
            team, flag = None, "no_team"
        elif len(found) == 1:
            team, flag = found.pop(), "ok"
        else:
            team, flag = None, "conflict"
        rows.append({"key": key, "team": team, "team_flag": flag})

    return pd.DataFrame(rows, columns=["key", "team", "team_flag"])