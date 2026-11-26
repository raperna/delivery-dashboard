import math


def _is_blank(value):
    """A blank cell arrives as None or NaN. A 0 is a real value, not a blank."""
    if value is None:
        return True
    return isinstance(value, float) and math.isnan(value)


def effective_points(value, default):
    """Return (points, defaulted) for one item.

    Blank points get the default and are flagged, so the warning can list them.
    Zero is kept as a real estimate.
    """
    if _is_blank(value):
        return default, True
    return value, False


def sprint_speed_mode(points, limit):
    """Decide how a sprint's speed and status are shown (D-019).

    `points` holds one value per committed item, with blanks as None or NaN.
    The sprint is assessed by velocity only if points exist and the share of
    blank items is at or below `limit`. Otherwise the status is Not assessed
    and throughput is shown instead.
    """
    total = len(points)
    if total == 0:
        return {"speed": "throughput", "status": "Not assessed"}

    blanks = sum(1 for value in points if _is_blank(value))
    if blanks == total:
        return {"speed": "throughput", "status": "Not assessed"}

    defaulted_share = blanks / total
    if defaulted_share > limit:
        return {"speed": "throughput", "status": "Not assessed"}
    return {"speed": "velocity", "status": "assessed"}