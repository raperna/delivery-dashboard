import statistics
from datetime import datetime, time

import pandas as pd

from dashboard.events import first_event_time, points_state
from dashboard.points import effective_points, sprint_speed_mode


def _end_of_day(day):
    return datetime.combine(day, time(23, 59, 59))


def cycle_time_summary(events, cutoff, started, done):
    """Calendar days from the first start to the first Done (D-029)."""
    starts = first_event_time(events, "status", started, cutoff)
    ends = first_event_time(events, "status", done, cutoff)
    days = []
    not_started = 0
    not_done = 0
    for key in set(starts) | set(ends):
        start = starts.get(key)
        end = ends.get(key)
        if start is None:
            not_started += 1
        elif end is None:
            not_done += 1
        elif end < start:
            not_started += 1
        else:
            days.append((end - start).days)
    summary = {
        "count": len(days),
        "median": None,
        "p85": None,
        "not_started": not_started,
        "not_done": not_done,
    }
    if days:
        summary["median"] = float(statistics.median(days))
        summary["p85"] = float(pd.Series(days).quantile(0.85))
    return summary


def sprint_metrics(events, start_date, end_date, done_statuses, settings):
    """Throughput and velocity for one sprint (D-028)."""
    completed_at = first_event_time(
        events, "status", done_statuses, _end_of_day(end_date)
    )
    completed = [key for key, when in completed_at.items() if when.date() >= start_date]
    points = points_state(events, _end_of_day(end_date))
    values = [points.get(key) for key in completed]
    mode = sprint_speed_mode(values, settings["max_defaulted_share"])
    velocity = None
    if mode["speed"] == "velocity":
        velocity = sum(
            effective_points(value, settings["default_points"])[0] for value in values
        )
    return {"throughput": len(completed), "velocity": velocity, "speed": mode["speed"]}


def rolling_average(values, window=3):
    """Average of the last `window` sprints, blank if any of them is blank (D-030)."""
    result = []
    for index in range(len(values)):
        if index + 1 < window:
            result.append(None)
            continue
        recent = values[index + 1 - window : index + 1]
        if any(value is None for value in recent):
            result.append(None)
        else:
            result.append(sum(recent) / window)
    return result