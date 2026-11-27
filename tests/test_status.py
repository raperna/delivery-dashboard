from dashboard.status import team_status

SETTINGS = {
    "midpoint_working_day": 5,
    "at_risk": 0.05,
    "off_track": 0.10,
    "max_defaulted_share": 0.20,
    "default_points": 1,
}


def items(count, points=1, done_count=0):
    """Build `count` committed items, the first `done_count` of them Done."""
    return [
        {"points": points, "done": index < done_count}
        for index in range(count)
    ]


def test_on_track_when_done_matches_expected():
    result = team_status(items(10, done_count=5), elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["status"] == "On track"


def test_too_early_before_midpoint():
    result = team_status(items(10), elapsed_days=4, sprint_days=10, settings=SETTINGS)
    assert result["status"] == "Too early"


def test_at_risk_at_five_percent():
    # 40 items of 1 point, 20 expected, 18 done: gap 2 = 5%
    result = team_status(items(40, done_count=18), elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["status"] == "At risk"


def test_off_track_at_ten_percent():
    # 40 items of 1 point, 20 expected, 16 done: gap 4 = 10%
    result = team_status(items(40, done_count=16), elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["status"] == "Off track"


def test_one_late_item_on_a_small_team_sets_status_by_percentage():
    # 10 items of 1 point, 5 expected, 4 done: gap 1 = 10%, so Off track (D-024)
    result = team_status(items(10, done_count=4), elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["status"] == "Off track"


def test_just_under_five_percent_is_on_track():
    # 100 items of 1 point, 50 expected, 47 done: gap 3 = 3%
    result = team_status(items(100, done_count=47), elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["status"] == "On track"


def test_ahead_of_plan_is_on_track():
    result = team_status(items(10, done_count=10), elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["status"] == "On track"


def test_defaulted_share_over_limit_is_not_assessed_with_throughput():
    # 3 of 10 blank = 30%, over the 20% limit
    mixed = [{"points": None, "done": False}] * 3 + items(7)
    result = team_status(mixed, elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["status"] == "Not assessed"
    assert result["speed"] == "throughput"
    assert result["throughput"] == 0


def test_blank_points_use_default_in_expected():
    # 8 items of 1 point and 2 blank (default 1): committed 10, expected 5 at midpoint
    mixed = items(8) + [{"points": None, "done": False}] * 2
    result = team_status(mixed, elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["committed"] == 10
    assert result["expected"] == 5


def test_only_done_items_count_as_done():
    result = team_status(items(10, done_count=3), elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["done"] == 3


def test_elapsed_is_capped_at_sprint_length():
    # Report run after sprint end: expected must equal committed, not exceed it
    result = team_status(items(10), elapsed_days=12, sprint_days=10, settings=SETTINGS)
    assert result["expected"] == 10


def test_zero_committed_points_is_not_assessed_with_throughput():
    result = team_status(items(5, points=0), elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["status"] == "Not assessed"
    assert result["speed"] == "throughput"


def test_no_committed_items_is_na():
    result = team_status([], elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["status"] == "Not assessed"
    assert result["speed"] == "N/A"


def test_not_assessed_numbers_are_blank():
    result = team_status(items(5, points=0), elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["committed"] is None
    assert result["expected"] is None
    assert result["done"] is None
    assert result["shortfall"] is None
    assert result["velocity"] is None


def test_velocity_is_done_points_when_assessed():
    result = team_status(items(10, done_count=5), elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["speed"] == "velocity"
    assert result["velocity"] == 5
    assert result["throughput"] is None


def test_throughput_counts_done_committed_items_when_not_assessed():
    mixed = [{"points": None, "done": False}] * 3 + items(7, done_count=4)
    result = team_status(mixed, elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["speed"] == "throughput"
    assert result["throughput"] == 4
    assert result["velocity"] is None


def test_zero_point_items_use_throughput():
    result = team_status(items(5, points=0, done_count=2), elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["speed"] == "throughput"
    assert result["throughput"] == 2


def test_no_items_has_no_velocity_or_throughput():
    result = team_status([], elapsed_days=5, sprint_days=10, settings=SETTINGS)
    assert result["velocity"] is None
    assert result["throughput"] is None