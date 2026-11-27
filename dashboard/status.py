from dashboard.points import effective_points, sprint_speed_mode


def _result(status, speed, committed=None, expected=None, done=None,
            shortfall=None, velocity=None, throughput=None):
    return {
        "status": status,
        "speed": speed,
        "committed": committed,
        "expected": expected,
        "done": done,
        "shortfall": shortfall,
        "velocity": velocity,
        "throughput": throughput,
    }


def team_status(items, elapsed_days, sprint_days, settings):
    """Status and speed for one team on one report date (D-023, D-024, D-034).

    items: list of dicts with 'points' (None when blank) and 'done' (bool).
    speed is one of:
      'velocity'   assessed; velocity holds points Done, throughput is None
      'throughput' Not assessed on points; throughput holds committed items Done
      'N/A'        no items committed; velocity and throughput are None
    """
    if not items:
        return _result("Not assessed", "N/A")

    done_items = sum(1 for item in items if item["done"])
    mode = sprint_speed_mode(
        [item["points"] for item in items], settings["max_defaulted_share"]
    )
    if mode["status"] == "Not assessed":
        return _result("Not assessed", "throughput", throughput=done_items)

    default = settings["default_points"]
    scored = [effective_points(item["points"], default)[0] for item in items]
    committed = sum(scored)
    if committed == 0:
        return _result("Not assessed", "throughput", throughput=done_items)

    done = sum(points for points, item in zip(scored, items) if item["done"])

    if elapsed_days < settings["midpoint_working_day"]:
        return _result("Too early", "velocity", committed=committed, velocity=done)

    elapsed = min(elapsed_days, sprint_days)
    expected = committed * elapsed / sprint_days
    shortfall = (expected - done) / committed

    if shortfall >= settings["off_track"]:
        status = "Off track"
    elif shortfall >= settings["at_risk"]:
        status = "At risk"
    else:
        status = "On track"
    return _result(status, "velocity", committed, expected, done, shortfall, velocity=done)