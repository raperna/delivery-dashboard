from dashboard.blocked import blocked_items
from dashboard.calendar import working_days_elapsed, working_days_in_sprint
from dashboard.signals import scope_changes, team_facts, where_to_look
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

    Each configured team gets its status, its scope changes, and its
    where-to-look prompts (US-07, US-08). The blocked list covers all teams.
    """
    teams = []
    for team in team_labels:
        result = team_report(events, sprint_name, start_date, end_date, report_date,
                             team, team_labels, done_statuses, holidays, settings)
        scope = scope_changes(events, sprint_name, start_date, report_date, team,
                              team_labels, settings["default_points"])
        facts = team_facts(events, sprint_name, start_date, report_date, team,
                           team_labels, done_statuses, blocked_statuses,
                           settings["default_points"])
        teams.append({
            "team": team,
            **result,
            "scope": scope,
            "prompts": where_to_look(result["status"], facts, scope),
        })

    return {
        "elapsed_days": working_days_elapsed(start_date, report_date, holidays),
        "sprint_days": working_days_in_sprint(start_date, end_date, holidays),
        "teams": teams,
        "blocked": blocked_items(events, report_date, blocked_statuses, team_labels, holidays),
    }