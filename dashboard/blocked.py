from datetime import datetime, time, timedelta

from dashboard.calendar import working_days_in_sprint
from dashboard.events import field_state, label_state, labels_on, last_change_time

UNASSIGNED = "Team Unassigned"


def _end_of_day(day):
    return datetime.combine(day, time(23, 59, 59))


def working_days_waiting(blocked_on, report_date, holidays):
    """Working days after the block date, up to and including the report date (D-033)."""
    return working_days_in_sprint(blocked_on + timedelta(days=1), report_date, holidays)


def blocked_items(events, report_date, blocked_statuses, team_labels, holidays):
    """Items blocked on report_date, longest wait first (D-027, D-025, D-033)."""
    cutoff = _end_of_day(report_date)
    statuses = field_state(events, "status", cutoff)
    since = last_change_time(events, "status", cutoff)
    labels = label_state(events, cutoff)
    assignees = field_state(events, "assignee", cutoff)
    team_lookup = {name.lower(): name for name in team_labels}

    rows = []
    for key, status in statuses.items():
        if status not in blocked_statuses:
            continue
        found = {
            team_lookup[label.lower()]
            for label in labels_on(labels, key)
            if label.lower() in team_lookup
        }
        if len(found) == 1:
            team, flag = found.pop(), "ok"
        elif len(found) == 0:
            team, flag = UNASSIGNED, "no_team"
        else:
            team, flag = UNASSIGNED, "conflict"
        waiting_since = since[key].date()
        rows.append({
            "key": key,
            "team": team,
            "team_flag": flag,
            "developer": assignees.get(key),
            "waiting_since": waiting_since,
            "days_waiting": working_days_waiting(waiting_since, report_date, holidays),
        })
    return sorted(rows, key=lambda row: row["days_waiting"], reverse=True)