from datetime import datetime, time

import pandas as pd

from dashboard.commitment import commitment_at_start
from dashboard.events import (
    field_state,
    label_state,
    labels_on,
    points_state,
    sprint_state,
)
from dashboard.points import effective_points
from dashboard.snapshot import team_items


def _end_of_day(day):
    return datetime.combine(day, time(23, 59, 59))


def _team_now(labels, key, team_lookup):
    found = {
        team_lookup[label.lower()]
        for label in labels_on(labels, key)
        if label.lower() in team_lookup
    }
    return found.pop() if len(found) == 1 else None


def scope_changes(events, sprint_name, start_date, report_date, team, team_labels, default_points):
    """Items added to or removed from one team's commitment after the start (US-07, D-039).

    Added: in the sprint on the report date, not committed at start, and on this
    team at the report date. Removed: committed at start, no longer in the sprint.
    Points for removed items are the start-day value; for added items, the
    report-date value. Blank points count as the default.
    """
    team_lookup = {name.lower(): name for name in team_labels}
    start_cut = _end_of_day(start_date)
    report_cut = _end_of_day(report_date)

    commitment = commitment_at_start(events, sprint_name, start_date, team_labels)
    committed = set(commitment.loc[commitment["team"] == team, "key"])
    members_now = {
        key for key, names in sprint_state(events, report_cut).items()
        if sprint_name in names
    }
    labels_now = label_state(events, report_cut)
    points_start = points_state(events, start_cut)
    points_now = points_state(events, report_cut)

    added = {
        key for key in members_now - committed
        if _team_now(labels_now, key, team_lookup) == team
    }
    removed = committed - members_now

    def total(keys, source):
        return sum(effective_points(source.get(key), default_points)[0] for key in keys)

    return {
        "added": {"count": len(added), "points": total(added, points_now)},
        "removed": {"count": len(removed), "points": total(removed, points_start)},
    }


def _blocked_during(events, blocked_statuses, start_cut, report_cut):
    """Keys with a move into a blocked status after the start day, up to the report date."""
    selected = events[events["field"] == "status"]
    created = pd.to_datetime(selected["created"])
    in_window = (created > pd.Timestamp(start_cut)) & (created <= pd.Timestamp(report_cut))
    is_blocked = selected["toString"].isin(blocked_statuses)
    return set(selected.loc[in_window & is_blocked, "key"])


def team_facts(events, sprint_name, start_date, report_date, team, team_labels,
               done_statuses, blocked_statuses, default_points):
    """Counts behind the where-to-look prompts for one team (US-08)."""
    start_cut = _end_of_day(start_date)
    report_cut = _end_of_day(report_date)
    items = team_items(events, sprint_name, start_date, team, team_labels,
                       done_statuses, report_date)
    committed_points = sum(
        effective_points(item["points"], default_points)[0] for item in items
    )
    open_keys = {item["key"] for item in items if not item["done"]}
    assignees = field_state(events, "assignee", report_cut)
    developers = {assignees[key] for key in open_keys if assignees.get(key)}
    blocked = _blocked_during(events, blocked_statuses, start_cut, report_cut)
    return {
        "committed_points": committed_points,
        "blank_items": sum(1 for item in items if item["points"] is None),
        "committed_items": len(items),
        "open_items": len(open_keys),
        "open_developers": len(developers),
        "unassigned_open": sum(1 for key in open_keys if not assignees.get(key)),
        "blocked_items": len({item["key"] for item in items} & blocked),
    }


def where_to_look(status, facts, scope):
    """Prompts for a team that is At risk or Off track (US-08, D-040).

    Each prompt states its figure and the data behind it. These are prompts
    for the team lead, not causes (D-010).
    """
    if status not in ("At risk", "Off track"):
        return []
    prompts = []
    added = scope["added"]["points"]
    removed = scope["removed"]["points"]

    if added or facts["blank_items"]:
        prompts.append({
            "area": "Estimation",
            "text": (
                f"{added:g} points were added after the sprint started, and "
                f"{facts['blank_items']} of {facts['committed_items']} committed "
                "items have no points."
            ),
        })
    if removed:
        prompts.append({
            "area": "Scope",
            "text": f"{removed:g} committed points were removed from the sprint. "
                    "Removed work still counts as not delivered (D-039).",
        })
    if facts["open_developers"]:
        per_developer = facts["open_items"] / facts["open_developers"]
        prompts.append({
            "area": "Resourcing",
            "text": (
                f"{facts['open_items']} items are open across "
                f"{facts['open_developers']} developers, about "
                f"{per_developer:.1f} each. This is a team figure, not per person."
            ),
        })
    elif facts["open_items"]:
        prompts.append({
            "area": "Resourcing",
            "text": f"{facts['open_items']} open items have no assignee.",
        })
    if facts["blocked_items"]:
        prompts.append({
            "area": "Technical or dependency",
            "text": (
                f"{facts['blocked_items']} of {facts['committed_items']} committed "
                "items were blocked during the sprint."
            ),
        })
    return prompts