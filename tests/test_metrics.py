from datetime import date, datetime

import pandas as pd
import pytest

from dashboard.metrics import cycle_time_summary, rolling_average, sprint_metrics

STARTED = {"In Progress"}
DONE = {"Done"}
SETTINGS = {"max_defaulted_share": 0.20, "default_points": 1}
START = date(2026, 3, 2)
END = date(2026, 3, 13)
CUTOFF = datetime(2026, 3, 13, 23, 59, 59)


def make_events(rows):
    return pd.DataFrame(
        rows, columns=["key", "created", "field", "fromString", "toString"]
    )


def status(key, when, to, frm=None):
    return [key, when, "status", frm, to]


def points(key, when, value, frm=None):
    return [key, when, "Story Points", frm, value]


def cycle(events, cutoff=CUTOFF):
    return cycle_time_summary(events, cutoff, STARTED, DONE)


def sprint(events):
    return sprint_metrics(events, START, END, DONE, SETTINGS)


def test_cycle_days_from_first_start_to_first_done():
    events = make_events([
        status("DEMO-1", "2026-03-02 09:00:00", "In Progress", "To Do"),
        status("DEMO-1", "2026-03-06 09:00:00", "Done", "In Progress"),
    ])
    result = cycle(events)
    assert result["count"] == 1
    assert result["median"] == 4.0


def test_done_without_a_start_is_counted_as_not_started():
    events = make_events([status("DEMO-1", "2026-03-06 09:00:00", "Done")])
    result = cycle(events)
    assert result["count"] == 0
    assert result["not_started"] == 1


def test_started_but_not_done_is_counted_as_not_done():
    events = make_events([status("DEMO-1", "2026-03-02 09:00:00", "In Progress")])
    result = cycle(events)
    assert result["count"] == 0
    assert result["not_done"] == 1


def test_done_after_cutoff_is_not_counted():
    events = make_events([
        status("DEMO-1", "2026-03-02 09:00:00", "In Progress"),
        status("DEMO-1", "2026-03-20 09:00:00", "Done", "In Progress"),
    ])
    result = cycle(events)
    assert result["count"] == 0
    assert result["not_done"] == 1


def test_median_and_p85_over_five_items():
    # Cycle times of 1, 2, 3, 4 and 5 days
    rows = []
    for index, day in enumerate(range(3, 8), start=1):
        key = f"DEMO-{index}"
        rows.append(status(key, "2026-03-02 09:00:00", "In Progress"))
        rows.append(status(key, f"2026-03-{day:02d} 09:00:00", "Done", "In Progress"))
    result = cycle(make_events(rows))
    assert result["median"] == 3.0
    assert result["p85"] == pytest.approx(4.4)


def test_reopened_then_redone_uses_first_done():
    events = make_events([
        status("DEMO-1", "2026-03-02 09:00:00", "In Progress"),
        status("DEMO-1", "2026-03-04 09:00:00", "Done", "In Progress"),
        status("DEMO-1", "2026-03-05 09:00:00", "In Progress", "Done"),
        status("DEMO-1", "2026-03-10 09:00:00", "Done", "In Progress"),
    ])
    assert cycle(events)["median"] == 2.0


def test_throughput_counts_completions_inside_the_window():
    events = make_events([
        status("DEMO-1", "2026-03-04 09:00:00", "Done", "In Progress"),
        status("DEMO-2", "2026-03-05 09:00:00", "Done", "In Progress"),
        status("DEMO-3", "2026-03-12 09:00:00", "Done", "In Progress"),
    ])
    assert sprint(events)["throughput"] == 3


def test_completion_outside_the_window_is_not_counted():
    events = make_events([
        status("DEMO-1", "2026-02-27 09:00:00", "Done", "In Progress"),
        status("DEMO-2", "2026-03-16 09:00:00", "Done", "In Progress"),
    ])
    assert sprint(events)["throughput"] == 0


def test_velocity_sums_points_and_defaults_one_blank_in_five():
    # Four pointed items (3, 5, 2, 2) and one blank: blank share 20%, at the limit
    rows = []
    for index, value in enumerate(["3", "5", "2", "2"], start=1):
        key = f"DEMO-{index}"
        rows.append(points(key, "2026-03-01 09:00:00", value))
        rows.append(status(key, f"2026-03-0{index + 3} 09:00:00", "Done", "In Progress"))
    rows.append(status("DEMO-5", "2026-03-08 09:00:00", "Done", "In Progress"))
    result = sprint(make_events(rows))
    assert result["throughput"] == 5
    assert result["velocity"] == 13.0


def test_velocity_is_none_when_completed_items_are_mostly_blank():
    rows = [points("DEMO-1", "2026-03-01 09:00:00", "5")]
    for index in range(1, 5):
        key = f"DEMO-{index}"
        rows.append(status(key, f"2026-03-0{index + 3} 09:00:00", "Done", "In Progress"))
    result = sprint(make_events(rows))
    assert result["throughput"] == 4
    assert result["velocity"] is None


def test_no_completions_gives_zero_throughput_and_no_velocity():
    result = sprint(make_events([]))
    assert result["throughput"] == 0
    assert result["velocity"] is None


def test_rolling_average_needs_three_sprints():
    assert rolling_average([6, 9, 12]) == [None, None, 9.0]


def test_rolling_average_is_blank_when_a_sprint_in_the_window_has_no_velocity():
    assert rolling_average([6, None, 12, 9]) == [None, None, None, None]

def test_cycle_time_counts_calendar_days_between_dates():
    # Started 2 March 12:00, Done 4 March 09:00: dates differ by 2 days
    events = make_events([
        status("DEMO-1", "2026-03-02 12:00:00", "In Progress", "To Do"),
        status("DEMO-1", "2026-03-04 09:00:00", "Done", "In Progress"),
    ])
    assert cycle(events)["median"] == 2.0


def test_same_day_completion_is_zero_days():
    events = make_events([
        status("DEMO-1", "2026-03-02 09:00:00", "In Progress", "To Do"),
        status("DEMO-1", "2026-03-02 17:00:00", "Done", "In Progress"),
    ])
    assert cycle(events)["median"] == 0.0


def test_overnight_completion_is_one_day():
    events = make_events([
        status("DEMO-1", "2026-03-02 17:00:00", "In Progress", "To Do"),
        status("DEMO-1", "2026-03-03 09:00:00", "Done", "In Progress"),
    ])
    assert cycle(events)["median"] == 1.0