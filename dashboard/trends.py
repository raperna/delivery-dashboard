import statistics
from datetime import date, datetime, time

from dashboard.calendar import working_days_in_sprint
from dashboard.events import first_event_time
from dashboard.metrics import rolling_average
from dashboard.snapshot import team_items
from dashboard.status import team_status


def _end_of_day(day):
    return datetime.combine(day, time(23, 59, 59))


def _cycle_median(events, keys, started, done, cutoff):
    """Median whole calendar days from first start to first Done, counted by date (D-036)."""
    starts = first_event_time(events, "status", started, cutoff)
    ends = first_event_time(events, "status", done, cutoff)
    days = [
        (ends[key].date() - starts[key].date()).days
        for key in keys
        if key in starts and key in ends and ends[key] >= starts[key]
    ]
    return float(statistics.median(days)) if days else None


def trend_for_team(events, sprints, team, team_labels, started, done, settings, holidays):
    """Per-sprint trend for one team (D-037).

    Status, speed and velocity come from team_status, with the whole sprint
    elapsed, so the trend and the status table use one rule. Throughput is the
    count of committed items Done by the sprint end date, for every sprint.
    Rolling velocity is the three-sprint average from D-030.
    """
    rows = []
    for name, start, end in sprints:
        items = team_items(events, name, start, team, team_labels, done, end)
        sprint_days = working_days_in_sprint(start, end, holidays)
        result = team_status(
            items, elapsed_days=sprint_days, sprint_days=sprint_days, settings=settings
        )
        done_keys = [item["key"] for item in items if item["done"]]
        rows.append({
            "sprint": name,
            "status": result["status"],
            "speed": result["speed"],
            "throughput": len(done_keys),
            "velocity": result["velocity"],
            "cycle_median": _cycle_median(events, done_keys, started, done, _end_of_day(end)),
        })

    for row, rolling in zip(rows, rolling_average([row["velocity"] for row in rows])):
        row["rolling_velocity"] = rolling
    return rows


def parse_sprint_lines(text):
    """Parse 'name, start, end' lines with ISO dates into sprint tuples, in the order typed.

    Splits from the right, so a sprint name may contain commas.
    """
    sprints = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            name, start, end = (part.strip() for part in line.rsplit(",", 2))
            sprints.append((name, date.fromisoformat(start), date.fromisoformat(end)))
        except ValueError as error:
            raise ValueError(
                f"Line {number} must be: name, YYYY-MM-DD, YYYY-MM-DD"
            ) from error
    return sprints