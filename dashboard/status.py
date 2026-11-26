from dashboard.points import effective_points, sprint_speed_mode


def _result(status, speed, committed=0, expected=None, done=None, shortfall=None):
    return {
        "status": status,
        "speed": speed,
        "committed": committed,
        "expected": expected,
        "done": done,
        "shortfall": shortfall,
    }


def team_status(items, elapsed_days, sprint_days, settings):
    """Status for one team's committed items on one report date (D-023, D-024).

    items: list of dicts with 'points' (None when blank) and 'done' (bool).
    elapsed_days: working days elapsed by the report date.
    sprint_days: working days in the sprint.
    The percentage thresholds alone decide the status.
    """
    default = settings["default_points"]
    mode = sprint_speed_mode(
        [item["points"] for item in items], settings["max_defaulted_share"]
    )
    if mode["status"] == "Not assessed":
        return _result("Not assessed", mode["speed"])

    scored = [effective_points(item["points"], default)[0] for item in items]
    committed = sum(scored)
    if committed == 0:
        return _result("Not assessed", "velocity")

    if elapsed_days < settings["midpoint_working_day"]:
        return _result("Too early", "velocity", committed=committed)

    elapsed = min(elapsed_days, sprint_days)
    expected = committed * elapsed / sprint_days
    done = sum(points for points, item in zip(scored, items) if item["done"])
    shortfall = (expected - done) / committed

    if shortfall >= settings["off_track"]:
        status = "Off track"
    elif shortfall >= settings["at_risk"]:
        status = "At risk"
    else:
        status = "On track"
    return _result(status, "velocity", committed, expected, done, shortfall)