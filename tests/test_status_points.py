from dashboard.points import effective_points, sprint_speed_mode


def test_item_with_points_keeps_its_value():
    assert effective_points(5, default=1) == (5, False)


def test_item_without_points_gets_default_and_is_flagged():
    assert effective_points(float("nan"), default=1) == (1, True)


def test_zero_points_is_a_real_value_not_a_gap():
    # A 0 means "estimated as trivial", not "not estimated". Only blank gets the default.
    assert effective_points(0, default=1) == (0, False)


def test_fully_unpointed_sprint_uses_throughput_and_no_status():
    mode = sprint_speed_mode(points=[None, None, None], limit=0.20)
    assert mode == {"speed": "throughput", "status": "Not assessed"}


def test_sprint_over_defaulted_limit_uses_throughput():
    # 3 of 10 items defaulted = 30%, over the 20% limit
    points = [5, 3, 2, 2, 1, 1, 1] + [None] * 3
    mode = sprint_speed_mode(points=points, limit=0.20)
    assert mode == {"speed": "throughput", "status": "Not assessed"}


def test_sprint_under_defaulted_limit_uses_velocity():
    # 1 of 10 items defaulted = 10%, under the 20% limit
    points = [5, 3, 2, 2, 1, 1, 1, 1, 1] + [None]
    mode = sprint_speed_mode(points=points, limit=0.20)
    assert mode == {"speed": "velocity", "status": "assessed"}


def test_zero_points_are_not_counted_as_defaulted():
    points = [0, 0, 0, 5]
    mode = sprint_speed_mode(points=points, limit=0.20)
    assert mode == {"speed": "velocity", "status": "assessed"}

def test_exactly_at_the_limit_is_still_assessed():
    # 2 of 10 items defaulted = 20%, exactly at the limit, which is not over it
    points = [5, 3, 2, 2, 1, 1, 1, 1] + [None] * 2
    mode = sprint_speed_mode(points=points, limit=0.20)
    assert mode == {"speed": "velocity", "status": "assessed"}