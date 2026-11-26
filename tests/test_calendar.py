from datetime import date
from pathlib import Path

from dashboard.calendar import (
    holidays_from_csv,
    is_working_day,
    working_days_elapsed,
    working_days_in_sprint,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "holidays_2026.csv"
HOLIDAYS = holidays_from_csv(FIXTURE)


def test_fixture_loads_all_fourteen_holidays():
    assert len(HOLIDAYS) == 14
    assert date(2026, 4, 3) in HOLIDAYS  # Good Friday


def test_weekday_is_a_working_day():
    assert is_working_day(date(2026, 3, 2), HOLIDAYS) is True  # Monday


def test_weekend_is_not_a_working_day():
    assert is_working_day(date(2026, 3, 7), HOLIDAYS) is False  # Saturday


def test_holiday_is_not_a_working_day():
    assert is_working_day(date(2026, 4, 3), HOLIDAYS) is False  # Good Friday


def test_two_week_sprint_without_holidays_has_ten_working_days():
    assert working_days_in_sprint(date(2026, 3, 2), date(2026, 3, 13), HOLIDAYS) == 10


def test_easter_sprint_loses_two_holidays():
    # Mon 30 Mar to Fri 10 Apr contains Good Friday and Easter Monday
    assert working_days_in_sprint(date(2026, 3, 30), date(2026, 4, 10), HOLIDAYS) == 8


def test_saturday_holiday_does_not_reduce_working_days():
    # 15 August 2026 is a Saturday, so the sprint keeps all ten days
    assert working_days_in_sprint(date(2026, 8, 10), date(2026, 8, 21), HOLIDAYS) == 10


def test_elapsed_counts_start_day_inclusively():
    # Mon 2, Tue 3, Wed 4 March
    assert working_days_elapsed(date(2026, 3, 2), date(2026, 3, 4), HOLIDAYS) == 3


def test_elapsed_skips_holidays():
    # Mon 30, Tue 31 Mar, Wed 1, Thu 2 Apr; Good Friday does not count
    assert working_days_elapsed(date(2026, 3, 30), date(2026, 4, 3), HOLIDAYS) == 4


def test_weekend_start_counts_from_first_working_day():
    # Starts on Saturday 7 March; by Monday 9 March only Monday has elapsed
    assert working_days_elapsed(date(2026, 3, 7), date(2026, 3, 9), HOLIDAYS) == 1


def test_no_days_elapsed_before_start():
    assert working_days_elapsed(date(2026, 3, 2), date(2026, 2, 27), HOLIDAYS) == 0


def test_midpoint_is_working_day_five_of_a_two_week_sprint():
    # Fifth working day of Mon 2 to Fri 13 March is Friday 6 March
    assert working_days_elapsed(date(2026, 3, 2), date(2026, 3, 6), HOLIDAYS) == 5