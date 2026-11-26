from datetime import datetime, time

from dashboard.calendar import working_days_elapsed, working_days_in_sprint
from dashboard.commitment import commitment_at_start
from dashboard.events import field_state, points_state, value_on
from dashboard.status import team_status


def _end_of_day(day):
    return datetime.combine(day, time(23, 59, 59))


def team_items(events, sprint_name, start_date, team, team_labels, done_statuses, report_date):
    """One team's committed items as they stand on report_date (D-026).

    Membership and team come from the end of the start day (D-020). Points are
    the value on the start day (D-021). Done means the status on report_date is
    one of done_statuses, given as raw Jira status names. Items with no team
    label, a conflicting team, or another team are left out.
    """
    commitment = commitment_at_start(events, sprint_name, start_date, team_labels)
    mine = commitment[commitment["team"] == team]
    points = points_state(events, _end_of_day(start_date))
    statuses = field_state(events, "status", _end_of_day(report_date))
    return [
        {
            "key": key,
            "points": points.get(key),
            "done": value_on(statuses, key) in done_statuses,
        }
        for key in mine["key"]
    ]


def team_report(events, sprint_name, start_date, end_date, report_date, team,
                team_labels, done_statuses, holidays, settings):
    """Status for one team on one report date: snapshot, then the status rule."""
    items = team_items(events, sprint_name, start_date, team, team_labels,
                       done_statuses, report_date)
    elapsed = working_days_elapsed(start_date, report_date, holidays)
    sprint_days = working_days_in_sprint(start_date, end_date, holidays)
    return team_status(items, elapsed, sprint_days, settings)