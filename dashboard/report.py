from dashboard.blocked import blocked_items
from dashboard.calendar import working_days_elapsed, working_days_in_sprint
from dashboard.snapshot import team_report
from dashboard.sprints import split_sprints


def sprint_names(events):
    """Every sprint name in the changelog, sorted, for the sprint selector."""
    names = set()
    for value in events.loc[events["field"] == "Sprint", "toString"]:
        names.update(split_sprints(value))
    return sorted(names)


def build_report(events, sprint_name, start_date, end_date, report_date, team_labels,
                 done_statuses, blocked_statuses, holidays, settings):
    """Everything the dashboard shows for one sprint on one report date (D-032).

    Each configured team gets its status from the snapshot and the status rules.
    A team with no committed items shows Not assessed. The blocked list covers
    all teams. The interface only displays this structure.
    """
    teams = []
    for team in team_labels:
        result = team_report(events, sprint_name, start_date, end_date, report_date,
                             team, team_labels, done_statuses, holidays, settings)
        teams.append({"team": team, **result})
    return {
        "elapsed_days": working_days_elapsed(start_date, report_date, holidays),
        "sprint_days": working_days_in_sprint(start_date, end_date, holidays),
        "teams": teams,
                "blocked": blocked_items(events, report_date, blocked_statuses, team_labels, holidays),
    }