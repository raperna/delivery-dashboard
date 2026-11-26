import csv
from datetime import date, timedelta


def holidays_from_csv(path):
    """Read the holiday fixture or export: one row per date, with a 'date' column."""
    with open(path, encoding="utf-8", newline="") as handle:
        return {date.fromisoformat(row["date"]) for row in csv.DictReader(handle)}


def is_working_day(day, holidays):
    """Monday to Friday, and not a listed holiday (D-022)."""
    return day.weekday() < 5 and day not in holidays


def _days_between(start, end):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def working_days_in_sprint(start, end, holidays):
    """Working days from start to end, both inclusive (D-022)."""
    return sum(1 for day in _days_between(start, end) if is_working_day(day, holidays))


def working_days_elapsed(start, as_of, holidays):
    """Working days from start to as_of, inclusive. Zero before the start (D-022)."""
    if as_of < start:
        return 0
    return working_days_in_sprint(start, as_of, holidays)