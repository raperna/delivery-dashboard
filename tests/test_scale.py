import time
from datetime import date, datetime

from dashboard.calendar import holidays_from_csv
from dashboard.config import (
    holiday_path,
    load_config,
    status_settings,
    statuses_mapped_to,
)
from dashboard.report import build_report
from dashboard.synthetic import END, SPRINT, START, TEAMS, build_scale_events

CONFIG = load_config()
HOLIDAYS = holidays_from_csv(holiday_path(CONFIG))
SETTINGS = status_settings(CONFIG)
DONE = statuses_mapped_to(CONFIG, "Done")
BLOCKED = statuses_mapped_to(CONFIG, "Blocked")
REPORT_DAY = date(2026, 3, 6)

ITEMS_PER_TEAM = 2500
DONE_PER_TEAM = {"Backend": 1250, "Frontend": 900, "DevOps": 1150, "QA": 1100}

# Hand-worked at day 5 of 10 (expected 1250 points per team):
# Backend shortfall 0%, Frontend 14%, DevOps 4%, QA 6%.
EXPECTED = {"Backend": "On track", "Frontend": "Off track", "DevOps": "On track", "QA": "At risk"}

# Set from the measurement in step 4. Local time x 5, floor of 10 seconds.
TIME_LIMIT_SECONDS = 5.0


def run_report(events):
    return build_report(
        events, SPRINT, START, END, REPORT_DAY, TEAMS, DONE, BLOCKED, HOLIDAYS, SETTINGS
    )


def test_generator_row_count_for_small_size():
    # Per item: sprint, labels, points, start = 4 rows. 40 items = 160 rows.
    # Done rows: 5 per team = 20 rows. Total 180.
    events = build_scale_events(items_per_team=10, done_per_team={team: 5 for team in TEAMS})
    assert len(events) == 180


def test_report_statuses_at_scale_match_hand_worked_answers():
    events = build_scale_events(ITEMS_PER_TEAM, DONE_PER_TEAM)
    statuses = {row["team"]: row["status"] for row in run_report(events)["teams"]}
    assert statuses == EXPECTED


def test_report_at_scale_completes_within_time_limit():
    # Only the report is timed. Building the events happens before the clock starts.
    events = build_scale_events(ITEMS_PER_TEAM, DONE_PER_TEAM)
    started = time.perf_counter()
    run_report(events)
    elapsed = time.perf_counter() - started
    assert elapsed < TIME_LIMIT_SECONDS

def test_replays_do_not_iterate_dataframe_rows():
    # Guards the optimisation: the replay code must not call DataFrame.iterrows
    import inspect

    import dashboard.events as events_module

    source = inspect.getsource(events_module)
    assert "iterrows" not in source

def test_replay_cache_does_not_leak_between_datasets():
    from dashboard.events import field_state

    first = build_scale_events(2, {"Backend": 2, "Frontend": 0, "DevOps": 0, "QA": 0})
    second = build_scale_events(2, {"Backend": 0, "Frontend": 0, "DevOps": 0, "QA": 0})
    cutoff = datetime(2026, 3, 6, 23, 59, 59)
    assert field_state(first, "status", cutoff)["BA-1"] == "Done"
    assert field_state(second, "status", cutoff)["BA-1"] == "In Progress"